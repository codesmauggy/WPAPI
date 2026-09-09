from django.db import transaction
from django.utils import timezone

from .models import (
    Campaign,
    CampaignRecipient,
    Conversation,
    Message,
)

from .services import send_template_message
from .campaign_events import broadcast_campaign_update


# ============================================================
# Exceptions
# ============================================================

class CampaignExecutionError(Exception):
    """Base campaign execution error."""


class CampaignEligibilityError(
    CampaignExecutionError
):
    """
    Raised when a recipient is not eligible
    to receive a campaign message.
    """


# ============================================================
# Execute Campaign
# ============================================================

def execute_campaign(
    campaign_id: int,
) -> dict:
    """
    Execute all PENDING recipients in a campaign.

    IMPORTANT:
    Only PENDING recipients are considered for sending.

    Safety rules:
    - Customer must be active.
    - Customer must have marketing consent.
    - Recipient must have a phone number.
    - SENT recipients are never resent.
    - DELIVERED recipients are never resent.
    - READ recipients are never resent.
    - CANCELLED recipients are never sent.
    """

    # --------------------------------------------------------
    # Load campaign
    # --------------------------------------------------------

    campaign = (
        Campaign.objects
        .select_related(
            "template",
            "phone_number",
            "audience",
        )
        .get(
            id=campaign_id
        )
    )

    # --------------------------------------------------------
    # Campaign validation
    # --------------------------------------------------------

    if campaign.status not in (
        "DRAFT",
        "SCHEDULED",
        "PAUSED",
    ):
        raise CampaignExecutionError(
            f"Campaign cannot be executed "
            f"from status: {campaign.status}"
        )

    # --------------------------------------------------------
    # Template validation
    # --------------------------------------------------------

    if campaign.template.status != "APPROVED":
        raise CampaignExecutionError(
            "Campaign template is not approved."
        )

    # --------------------------------------------------------
    # Get PENDING recipients only
    # --------------------------------------------------------

    recipients = (
        CampaignRecipient.objects
        .select_related(
            "customer",
            "campaign",
        )
        .filter(
            campaign=campaign,
            status="PENDING",
        )
        .order_by("id")
    )

    total = recipients.count()

    if total == 0:
        raise CampaignExecutionError(
            "Campaign has no PENDING recipients."
        )

    # --------------------------------------------------------
    # Start campaign
    # --------------------------------------------------------

    campaign.status = "RUNNING"

    campaign.started_at = timezone.now()

    campaign.save(
        update_fields=[
            "status",
            "started_at",
            "updated_at",
        ]
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {
        "campaign_id": campaign.id,
        "total": total,
        "sent": 0,
        "failed": 0,
        "cancelled": 0,
    }

    # --------------------------------------------------------
    # Send recipients
    # --------------------------------------------------------

    for recipient in recipients:

        try:

            send_campaign_recipient(
                campaign=campaign,
                recipient=recipient,
            )

            result["sent"] += 1

        except CampaignEligibilityError as exc:

            # ------------------------------------------------
            # Eligibility failures are NOT API failures.
            #
            # Example:
            # Customer opted out after recipient generation.
            #
            # We mark the recipient CANCELLED.
            # ------------------------------------------------

            recipient.status = "CANCELLED"

            recipient.error_message = str(exc)

            recipient.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            result["cancelled"] += 1

            print(
                f"Campaign recipient "
                f"{recipient.id} cancelled: "
                f"{exc}"
            )

        except Exception as exc:

            # ------------------------------------------------
            # Actual sending/API failure
            # ------------------------------------------------

            recipient.status = "FAILED"

            recipient.failed_at = timezone.now()

            recipient.error_message = str(exc)

            recipient.save(
                update_fields=[
                    "status",
                    "failed_at",
                    "error_message",
                    "updated_at",
                ]
            )

            result["failed"] += 1

            print(
                f"Campaign recipient "
                f"{recipient.id} failed: "
                f"{exc}"
            )

    # --------------------------------------------------------
    # Update campaign statistics
    # --------------------------------------------------------

    update_campaign_statistics(
        campaign
    )

    # --------------------------------------------------------
    # Complete campaign if nothing is pending
    # --------------------------------------------------------

    pending_count = (
        CampaignRecipient.objects
        .filter(
            campaign=campaign,
            status__in=[
                "PENDING",
                "SENDING",
            ],
        )
        .count()
    )

    if pending_count == 0:

        campaign.status = "COMPLETED"

        campaign.completed_at = (
            timezone.now()
        )

        campaign.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

    return result


# ============================================================
# Send One Campaign Recipient
# ============================================================

def send_campaign_recipient(
    campaign,
    recipient,
):
    """
    Send exactly one campaign recipient.

    The recipient is atomically claimed from PENDING
    to SENDING before the WhatsApp API is called.

    This prevents two workers from sending the same
    recipient simultaneously.
    """

    # --------------------------------------------------------
    # Atomically claim recipient
    # --------------------------------------------------------

    with transaction.atomic():

        claimed = (
            CampaignRecipient.objects
            .select_for_update()
            .filter(
                id=recipient.id,
                status="QUEUED",
            )
            .update(
                status="SENDING",
                updated_at=timezone.now(),
            )
        )

        if claimed != 1:

            # Someone else already claimed it,
            # or it is no longer pending.

            recipient.refresh_from_db()

            raise CampaignExecutionError(
                f"Recipient {recipient.id} could not "
                f"be claimed. Current status: "
                f"{recipient.status}"
            )

        # ----------------------------------------------------
        # Refresh locked/claimed recipient
        # ----------------------------------------------------

        recipient = (
            CampaignRecipient.objects
            .select_related(
                "customer",
                "campaign",
            )
            .get(
                id=recipient.id
            )
        )

    broadcast_campaign_update(
        campaign_id=campaign.id,
        recipient_id=recipient.id,
    )

    # --------------------------------------------------------
    # Customer safety checks
    #
    # These happen AFTER claiming the recipient.
    # If the customer is no longer eligible, we cancel it.
    # --------------------------------------------------------

    customer = recipient.customer

    if not customer:

        recipient.status = "CANCELLED"

        recipient.error_message = (
            "Recipient has no customer."
        )

        recipient.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        broadcast_campaign_update(campaign.id, recipient.id)

        raise CampaignEligibilityError(
            "Recipient has no customer."
        )

    # --------------------------------------------------------
    # Customer active check
    # --------------------------------------------------------

    if not customer.is_active:

        recipient.status = "CANCELLED"

        recipient.error_message = (
            "Customer is inactive. "
            "Campaign message was not sent."
        )

        recipient.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        broadcast_campaign_update(campaign.id, recipient.id)

        raise CampaignEligibilityError(
            "Customer is inactive. "
            "Campaign message was not sent."
        )

    # --------------------------------------------------------
    # Marketing consent check
    # --------------------------------------------------------

    if not customer.marketing_opted_in:

        recipient.status = "CANCELLED"

        recipient.error_message = (
            "Customer has not opted in to "
            "marketing messages. "
            "Campaign message was not sent."
        )

        recipient.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        broadcast_campaign_update(campaign.id, recipient.id)

        raise CampaignEligibilityError(
            "Customer has not opted in to "
            "marketing messages. "
            "Campaign message was not sent."
        )

    # --------------------------------------------------------
    # Customer phone check
    # --------------------------------------------------------

    if not customer.phone:

        recipient.status = "CANCELLED"

        recipient.error_message = (
            "Customer has no phone number."
        )

        recipient.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        broadcast_campaign_update(campaign.id, recipient.id)

        raise CampaignEligibilityError(
            "Customer has no phone number."
        )

    # --------------------------------------------------------
    # Recipient phone check
    # --------------------------------------------------------

    if not recipient.phone:

        recipient.status = "CANCELLED"

        recipient.error_message = (
            "Recipient has no phone number."
        )

        recipient.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        broadcast_campaign_update(campaign.id, recipient.id)

        raise CampaignEligibilityError(
            "Recipient has no phone number."
        )

    # --------------------------------------------------------
    # Build template components
    # --------------------------------------------------------

    try:

        components = build_template_components(
            recipient.variables
        )

        # ----------------------------------------------------
        # Send through WhatsApp
        # ----------------------------------------------------

        result = send_template_message(
            recipient_phone=recipient.phone,
            template_name=campaign.template.name,
            language_code=campaign.template.language,
            components=components,
        )

        # ----------------------------------------------------
        # Extract WhatsApp message ID
        # ----------------------------------------------------

        messages = result.get(
            "messages",
            [],
        )

        whatsapp_message_id = None

        if messages:

            whatsapp_message_id = (
                messages[0].get("id")
            )

        if not whatsapp_message_id:

            raise CampaignExecutionError(
                "Meta did not return a WhatsApp "
                "message ID."
            )

        # ----------------------------------------------------
        # Conversation
        # ----------------------------------------------------

        conversation = (
            get_or_create_conversation(
                campaign=campaign,
                recipient=recipient,
            )
        )

        # ----------------------------------------------------
        # Local Message
        # ----------------------------------------------------

        message = Message.objects.create(

            conversation=conversation,

            whatsapp_message_id=(
                whatsapp_message_id
            ),

            direction="outbound",

            message_type="template",

            text=(
                f"Template: "
                f"{campaign.template.name}"
            ),

            status="sent",

            raw_payload=result,
        )

        # ----------------------------------------------------
        # Update CampaignRecipient
        # ----------------------------------------------------

        recipient.message = message

        recipient.whatsapp_message_id = (
            whatsapp_message_id
        )

        recipient.status = "SENT"

        recipient.sent_at = timezone.now()

        recipient.error_message = ""

        recipient.save(
            update_fields=[
                "message",
                "whatsapp_message_id",
                "status",
                "sent_at",
                "error_message",
                "updated_at",
            ]
        )

        # Keep the persisted Campaign counters synchronized with
        # the recipient record immediately after a successful send.
        update_campaign_statistics(campaign)

        return message

    except CampaignEligibilityError:

        raise

    except Exception as exc:

        # ----------------------------------------------------
        # Meta/API failure
        # ----------------------------------------------------

        recipient.status = "FAILED"

        recipient.failed_at = timezone.now()

        recipient.error_message = str(exc)

        recipient.save(
            update_fields=[
                "status",
                "failed_at",
                "error_message",
                "updated_at",
            ]
        )

        # Keep the persisted Campaign counters synchronized even
        # when Meta rejects the send before a WhatsApp message ID
        # exists and no webhook can arrive for this failure.
        update_campaign_statistics(campaign)

        raise


# ============================================================
# Update Campaign Statistics
# ============================================================

def update_campaign_statistics(
    campaign,
):
    """Recalculate persisted campaign counters and broadcast the live state."""

    recipients = CampaignRecipient.objects.filter(campaign=campaign)

    total = recipients.count()
    pending = recipients.filter(status="PENDING").count()
    queued = recipients.filter(status="QUEUED").count()
    sending = recipients.filter(status="SENDING").count()
    sent = recipients.filter(status__in=["SENT", "DELIVERED", "READ"]).count()
    delivered = recipients.filter(status__in=["DELIVERED", "READ"]).count()
    read = recipients.filter(status="READ").count()
    failed = recipients.filter(status="FAILED").count()
    cancelled = recipients.filter(status="CANCELLED").count()

    campaign.total_recipients = total
    campaign.sent_count = sent
    campaign.delivered_count = delivered
    campaign.read_count = read
    campaign.failed_count = failed

    if (
        total > 0
        and pending == 0
        and queued == 0
        and sending == 0
        and sent + failed + cancelled >= total
        and campaign.status == "RUNNING"
    ):
        campaign.status = "COMPLETED"
        if not campaign.completed_at:
            campaign.completed_at = timezone.now()

    campaign.save(
        update_fields=[
            "total_recipients",
            "sent_count",
            "delivered_count",
            "read_count",
            "failed_count",
            "status",
            "completed_at",
            "updated_at",
        ]
    )

    broadcast_campaign_update(campaign.id)


# ============================================================
# Build Template Components
# ============================================================

def build_template_components(
    variables: dict,
):
    """
    Convert our variables dictionary into Meta
    WhatsApp template body parameters.

    Example:

        {
            "1": "Digital Express",
            "2": "500"
        }

    becomes:

        [
            {
                "type": "body",
                "parameters": [
                    {
                        "type": "text",
                        "text": "Digital Express"
                    },
                    {
                        "type": "text",
                        "text": "500"
                    }
                ]
            }
        ]
    """

    if not variables:

        return None

    parameters = []

    for key in sorted(
        variables.keys(),
        key=lambda value: (
            int(value)
            if str(value).isdigit()
            else str(value)
        ),
    ):

        parameters.append(
            {
                "type": "text",
                "text": str(
                    variables[key]
                ),
            }
        )

    return [
        {
            "type": "body",
            "parameters": parameters,
        }
    ]


# ============================================================
# Get or Create Conversation
# ============================================================

def get_or_create_conversation(
    campaign,
    recipient,
):
    """
    Get an existing open conversation for the customer
    and business WhatsApp number.

    If one doesn't exist, create it.
    """

    conversation = (
        Conversation.objects
        .filter(
            customer=recipient.customer,
            phone_number=campaign.phone_number,
            status="open",
        )
        .order_by("-created_at")
        .first()
    )

    if conversation:

        return conversation

    return Conversation.objects.create(
        customer=recipient.customer,
        phone_number=campaign.phone_number,
        status="open",
    )