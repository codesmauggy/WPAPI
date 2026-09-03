from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    WhatsAppPhoneNumber,
    Customer,
    Conversation,
    Message,
    CampaignRecipient,
)

from .services import send_text_message


def process_whatsapp_webhook(payload: dict) -> None:
    """
    Process a WhatsApp webhook payload.
    """

    if payload.get("object") != "whatsapp_business_account":
        return

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):

            if change.get("field") != "messages":
                continue

            value = change.get("value", {})

            process_message_event(value)


def process_message_event(value: dict) -> None:
    """
    Process incoming WhatsApp messages and message statuses.
    """

    metadata = value.get("metadata", {})

    phone_number_id = metadata.get(
        "phone_number_id"
    )

    display_phone_number = metadata.get(
        "display_phone_number",
        "",
    )

    if not phone_number_id:
        return

    phone_number = get_or_create_phone_number(
        phone_number_id=phone_number_id,
        display_phone_number=display_phone_number,
    )

    contacts = value.get("contacts", [])

    contact_map = {
        contact.get("wa_id"): contact
        for contact in contacts
    }

    # Incoming customer messages
    for message_data in value.get(
        "messages",
        [],
    ):
        process_incoming_message(
            phone_number=phone_number,
            message_data=message_data,
            contact_map=contact_map,
        )

    # Outgoing message status updates
    for status_data in value.get(
        "statuses",
        [],
    ):
        process_message_status(
            status_data=status_data,
        )


def get_or_create_phone_number(
    phone_number_id: str,
    display_phone_number: str,
):
    """
    Find the WhatsApp phone number registered
    in our system.

    For the development phase we automatically
    create it if it does not exist.
    """

    phone_number = (
        WhatsAppPhoneNumber.objects
        .filter(
            phone_number_id=phone_number_id
        )
        .first()
    )

    if phone_number:
        return phone_number

    business_account_id = (
        settings.WHATSAPP_BUSINESS_ACCOUNT_ID
    )

    from .models import WhatsAppBusinessAccount

    business_account, _ = (
        WhatsAppBusinessAccount.objects
        .get_or_create(
            business_account_id=business_account_id or None,
            defaults={
                "name": "WhatsApp Business Account",
            },
        )
    )

    phone_number = (
        WhatsAppPhoneNumber.objects
        .create(
            business_account=business_account,
            display_name=display_phone_number
            or "WhatsApp Number",
            phone_number=display_phone_number,
            phone_number_id=phone_number_id,
        )
    )

    return phone_number


def process_incoming_message(
    phone_number,
    message_data: dict,
    contact_map: dict,
):
    whatsapp_message_id = message_data.get("id")
    sender = message_data.get("from")

    if not whatsapp_message_id or not sender:
        return

    # Idempotency:
    # Meta may retry webhook events.
    if Message.objects.filter(
        whatsapp_message_id=whatsapp_message_id
    ).exists():
        return

    contact = contact_map.get(sender, {})

    profile = contact.get("profile", {})

    customer_name = profile.get(
        "name",
        "",
    )

    customer, _ = Customer.objects.get_or_create(
        whatsapp_id=sender,
        defaults={
            "name": customer_name,
            "phone": sender,
        },
    )

    if customer_name and not customer.name:
        customer.name = customer_name
        customer.save(
            update_fields=["name", "updated_at"]
        )

    conversation = (
        Conversation.objects
        .filter(
            customer=customer,
            phone_number=phone_number,
            status="open",
        )
        .order_by("-created_at")
        .first()
    )

    if not conversation:
        conversation = Conversation.objects.create(
            customer=customer,
            phone_number=phone_number,
            status="open",
        )

    message_type = message_data.get(
        "type",
        "unknown",
    )

    text = ""

    if message_type == "text":
        text = (
            message_data
            .get("text", {})
            .get("body", "")
        )

    message = Message.objects.create(
        conversation=conversation,
        whatsapp_message_id=whatsapp_message_id,
        direction="inbound",
        message_type=message_type,
        text=text,
        status="received",
        raw_payload=message_data,
    )

    conversation.last_message_at = timezone.now()
    conversation.save(
        update_fields=[
            "last_message_at",
            "updated_at",
        ]
    )

    print(
        f"Incoming WhatsApp message "
        f"from {sender}: {text}"
    )

    # First automated response.
    if message_type == "text":
        try:
            send_initial_reply(
                customer=customer,
                conversation=conversation,
                text=text,
            )
        except Exception as exc:
            print(
                "Failed to send WhatsApp reply:"
            )
            print(exc)

def process_message_status(
    status_data: dict,
) -> None:
    """
    Process WhatsApp outbound message status updates.

    Updates:
        1. Message
        2. CampaignRecipient
        3. Campaign counters
    """

    whatsapp_message_id = status_data.get("id")
    status = status_data.get("status")

    if not whatsapp_message_id or not status:
        return

    allowed_statuses = {
        "sent",
        "delivered",
        "read",
        "failed",
    }

    if status not in allowed_statuses:
        return

    # ---------------------------------------------------------
    # 1. Find local Message
    # ---------------------------------------------------------

    message = (
        Message.objects
        .select_related(
            "conversation",
        )
        .filter(
            whatsapp_message_id=whatsapp_message_id
        )
        .first()
    )

    if not message:
        print(
            "Status received for unknown "
            f"message: {whatsapp_message_id}"
        )
        return

    # ---------------------------------------------------------
    # 2. Update Message
    # ---------------------------------------------------------

    message.status = status

    if status == "failed":
        message.raw_payload = status_data

    message.save(
        update_fields=[
            "status",
            "raw_payload",
        ]
    )

    print(
        f"WhatsApp message "
        f"{whatsapp_message_id} "
        f"status updated to: {status}"
    )

    # ---------------------------------------------------------
    # 3. Find CampaignRecipient
    # ---------------------------------------------------------

    campaign_recipient = (
        CampaignRecipient.objects
        .select_related(
            "campaign",
        )
        .filter(
            whatsapp_message_id=(
                whatsapp_message_id
            )
        )
        .first()
    )

    if not campaign_recipient:
        print(
            "No CampaignRecipient found for "
            f"message {whatsapp_message_id}"
        )
        return

    now = timezone.now()

    # ---------------------------------------------------------
    # 4. Update CampaignRecipient
    # ---------------------------------------------------------

    update_fields = [
        "status",
        "updated_at",
    ]

    if status == "sent":

        campaign_recipient.status = "SENT"

        if not campaign_recipient.sent_at:
            campaign_recipient.sent_at = now
            update_fields.append("sent_at")

    elif status == "delivered":

        campaign_recipient.status = "DELIVERED"

        if not campaign_recipient.delivered_at:
            campaign_recipient.delivered_at = now
            update_fields.append("delivered_at")

    elif status == "read":

        campaign_recipient.status = "READ"

        if not campaign_recipient.read_at:
            campaign_recipient.read_at = now
            update_fields.append("read_at")

    elif status == "failed":

        campaign_recipient.status = "FAILED"
        campaign_recipient.failed_at = now
        campaign_recipient.error_message = (
            extract_whatsapp_error(
                status_data
            )
        )

        update_fields.extend([
            "failed_at",
            "error_message",
        ])

    campaign_recipient.save(
        update_fields=update_fields
    )

    print(
        f"Campaign recipient "
        f"{campaign_recipient.id} "
        f"status updated to: "
        f"{campaign_recipient.status}"
    )

    # ---------------------------------------------------------
    # 5. Update Campaign counters
    # ---------------------------------------------------------

    update_campaign_counters(
        campaign_recipient.campaign
    )

def extract_whatsapp_error(
    status_data: dict,
) -> str:
    """
    Extract a readable error message from
    a WhatsApp failed status event.
    """

    errors = status_data.get(
        "errors",
        [],
    )

    if not errors:
        return "WhatsApp message failed."

    messages = []

    for error in errors:

        message = error.get(
            "message"
        )

        code = error.get(
            "code"
        )

        if code and message:
            messages.append(
                f"{code}: {message}"
            )

        elif message:
            messages.append(message)

        elif code:
            messages.append(
                f"Error code {code}"
            )

    return "; ".join(messages) or (
        "WhatsApp message failed."
    )

def extract_whatsapp_error(
    status_data: dict,
) -> str:
    """
    Extract a readable error message from
    a WhatsApp failed status event.
    """

    errors = status_data.get(
        "errors",
        [],
    )

    if not errors:
        return "WhatsApp message failed."

    messages = []

    for error in errors:

        message = error.get(
            "message"
        )

        code = error.get(
            "code"
        )

        if code and message:
            messages.append(
                f"{code}: {message}"
            )

        elif message:
            messages.append(message)

        elif code:
            messages.append(
                f"Error code {code}"
            )

    return "; ".join(messages) or (
        "WhatsApp message failed."
    )

def update_campaign_counters(
    campaign,
) -> None:
    """
    Recalculate campaign statistics from
    CampaignRecipient records.

    Automatically marks the campaign as COMPLETED
    when every recipient has reached a terminal state.
    """

    recipients = (
        CampaignRecipient.objects
        .filter(
            campaign=campaign
        )
    )

    # ---------------------------------------------------------
    # Counts
    # ---------------------------------------------------------

    total = recipients.count()

    pending = (
        recipients
        .filter(
            status="PENDING"
        )
        .count()
    )

    sending = (
        recipients
        .filter(
            status="SENDING"
        )
        .count()
    )

    sent = (
        recipients
        .filter(
            status="SENT"
        )
        .count()
    )

    delivered = (
        recipients
        .filter(
            status="DELIVERED"
        )
        .count()
    )

    read = (
        recipients
        .filter(
            status="READ"
        )
        .count()
    )

    failed = (
        recipients
        .filter(
            status="FAILED"
        )
        .count()
    )

    cancelled = (
        recipients
        .filter(
            status="CANCELLED"
        )
        .count()
    )

    # ---------------------------------------------------------
    # Campaign statistics
    # ---------------------------------------------------------

    campaign.total_recipients = total

    campaign.sent_count = (
        recipients
        .filter(
            status__in=[
                "SENT",
                "DELIVERED",
                "READ",
            ]
        )
        .count()
    )

    campaign.delivered_count = (
        recipients
        .filter(
            status__in=[
                "DELIVERED",
                "READ",
            ]
        )
        .count()
    )

    campaign.read_count = read

    campaign.failed_count = failed

    # ---------------------------------------------------------
    # Determine whether campaign is completed
    # ---------------------------------------------------------

    completed = (
        sent
        + delivered
        + read
        + failed
        + cancelled
    )

    if (
        total > 0
        and pending == 0
        and sending == 0
        and completed == total
    ):
        campaign.status = "COMPLETED"

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    campaign.save(
        update_fields=[
            "total_recipients",
            "sent_count",
            "delivered_count",
            "read_count",
            "failed_count",
            "status",
            "updated_at",
        ]
    )

    print(
        f"Campaign {campaign.id} counters updated: "
        f"total={total}, "
        f"sent={campaign.sent_count}, "
        f"delivered={campaign.delivered_count}, "
        f"read={campaign.read_count}, "
        f"failed={campaign.failed_count}, "
        f"cancelled={cancelled}, "
        f"completed={completed}, "
        f"status={campaign.status}"
    )


def send_initial_reply(
    customer,
    conversation,
    text: str,
):
    reply = (
        "Hello! 👋\n\n"
        "Your WhatsApp connection is working "
        "successfully.\n\n"
        "We received your message."
    )

    try:
        result = send_text_message(
            recipient_phone=customer.phone,
            message=reply,
        )

        whatsapp_message_id = None

        messages = result.get(
            "messages",
            [],
        )

        if messages:
            whatsapp_message_id = messages[0].get(
                "id"
            )

        Message.objects.create(
            conversation=conversation,
            whatsapp_message_id=whatsapp_message_id,
            direction="outbound",
            message_type="text",
            text=reply,
            status="sent",
            raw_payload=result,
        )

        conversation.last_message_at = timezone.now()

        conversation.save(
            update_fields=[
                "last_message_at",
                "updated_at",
            ]
        )

        print(
            "WhatsApp reply sent successfully."
        )

    except Exception as exc:

        print(
            "WhatsApp reply failed:"
        )
        print(exc)

        Message.objects.create(
            conversation=conversation,
            direction="outbound",
            message_type="text",
            text=reply,
            status="failed",
            raw_payload={
                "error": str(exc),
            },
        )

        raise