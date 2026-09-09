from celery import shared_task
from django.utils import timezone
from .outbound import send_outbound_message
from .webhooks import process_whatsapp_webhook
from .campaigns import (
    CampaignEligibilityError,
    CampaignExecutionError,
    send_campaign_recipient,
)

from .models import (
    Campaign,
    CampaignRecipient,
)

from .dispatcher import (
    get_next_recipient,
)

from .rate_limiter import (
    reserve_send_slot,
)
from .campaign_events import broadcast_campaign_update


# ============================================================
# Send One Campaign Recipient
# ============================================================

@shared_task(
    bind=True,
)
def send_campaign_recipient_task(
    self,
    recipient_id: int,
    slot_reserved: bool = False,
):
    """
    Send exactly one campaign recipient.

    Recipient lifecycle:

        PENDING
            ↓
        QUEUED
            ↓
        SENDING
            ↓
        SENT / FAILED / CANCELLED

    The dispatcher changes PENDING → QUEUED.

    This task handles the global sending interval and then
    sends the recipient.
    """

    # --------------------------------------------------------
    # Load recipient
    # --------------------------------------------------------

    try:

        recipient = (
            CampaignRecipient.objects
            .select_related(
                "campaign",
                "customer",
            )
            .get(
                id=recipient_id,
            )
        )

    except CampaignRecipient.DoesNotExist:

        return {
            "success": False,
            "recipient_id": recipient_id,
            "status": "NOT_FOUND",
        }

    campaign = recipient.campaign

    # ========================================================
    # Recipient state
    # ========================================================

    # A recipient may be QUEUED when dispatched.

    if recipient.status not in (
        "QUEUED",
        "PENDING",
    ):

        return {
            "success": False,
            "recipient_id": recipient.id,
            "status": recipient.status,
            "message": (
                "Recipient is no longer available "
                "for sending."
            ),
        }

    # --------------------------------------------------------
    # Campaign must still be RUNNING
    # --------------------------------------------------------

    if campaign.status != "RUNNING":

        # If the campaign was paused before the task ran,
        # return the recipient to PENDING so Resume can process it.

        if recipient.status == "QUEUED":

            recipient.status = "PENDING"

            recipient.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            broadcast_campaign_update(
                campaign.id,
                recipient.id,
            )

        return {
            "success": False,
            "recipient_id": recipient.id,
            "status": recipient.status,
            "campaign_status": campaign.status,
            "message": (
                "Campaign is not RUNNING. "
                "Recipient was not sent."
            ),
        }

    # ========================================================
    # GLOBAL SENDING RATE CONTROL
    # ========================================================

    if not slot_reserved:

        delay = reserve_send_slot()

        # ----------------------------------------------------
        # Slot is in the future
        # ----------------------------------------------------

        if delay > 0:

            send_campaign_recipient_task.apply_async(
                args=[
                    recipient.id,
                ],
                kwargs={
                    "slot_reserved": True,
                },
                countdown=delay,
            )

            print(
                "WhatsApp recipient "
                f"{recipient.id} scheduled in "
                f"{delay:.2f} seconds."
            )

            return {
                "success": True,
                "recipient_id": recipient.id,
                "status": "SCHEDULED",
                "delay": delay,
            }

        # ----------------------------------------------------
        # Slot available immediately
        # ----------------------------------------------------

        print(
            "WhatsApp recipient "
            f"{recipient.id} sending immediately."
        )

    else:

        print(
            "WhatsApp recipient "
            f"{recipient.id} using reserved "
            "global sending slot."
        )

    # ========================================================
    # FINAL CAMPAIGN / RECIPIENT CHECK
    # ========================================================

    recipient.refresh_from_db(
        fields=[
            "status",
            "campaign",
        ]
    )

    campaign.refresh_from_db(
        fields=[
            "status",
        ]
    )

    # --------------------------------------------------------
    # Recipient must still be QUEUED or PENDING
    # --------------------------------------------------------

    if recipient.status not in (
        "QUEUED",
        "PENDING",
    ):

        return {
            "success": False,
            "recipient_id": recipient.id,
            "status": recipient.status,
            "message": (
                "Recipient changed state while "
                "waiting. Nothing was sent."
            ),
        }

    # --------------------------------------------------------
    # Campaign must still be RUNNING
    # --------------------------------------------------------

    if campaign.status != "RUNNING":

        if recipient.status == "QUEUED":

            recipient.status = "PENDING"

            recipient.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            broadcast_campaign_update(
                campaign.id,
                recipient.id,
            )

        return {
            "success": False,
            "recipient_id": recipient.id,
            "status": recipient.status,
            "campaign_status": campaign.status,
            "message": (
                "Campaign was paused or cancelled "
                "before the reserved send slot. "
                "Nothing was sent."
            ),
        }

    # ========================================================
    # SEND TO WHATSAPP
    # ========================================================

    try:

        message = send_campaign_recipient(
            campaign=campaign,
            recipient=recipient,
        )

        print(
            "WhatsApp recipient "
            f"{recipient.id} sent successfully."
        )

        return {
            "success": True,
            "recipient_id": recipient.id,
            "status": "SENT",
            "message_id": (
                message.whatsapp_message_id
            ),
        }

    # --------------------------------------------------------
    # Eligibility failure
    # --------------------------------------------------------

    except CampaignEligibilityError as exc:

        print(
            "Campaign eligibility error for "
            f"recipient {recipient.id}: {exc}"
        )

        return {
            "success": False,
            "recipient_id": recipient.id,
            "status": "CANCELLED",
            "error": str(exc),
        }

    # --------------------------------------------------------
    # Campaign execution failure
    # --------------------------------------------------------

    except CampaignExecutionError as exc:

        print(
            "Campaign execution error for "
            f"recipient {recipient.id}: {exc}"
        )

        return {
            "success": False,
            "recipient_id": recipient.id,
            "status": "FAILED",
            "error": str(exc),
        }

    # --------------------------------------------------------
    # Unexpected failure
    # --------------------------------------------------------

    except Exception as exc:

        print(
            "Unexpected error sending recipient "
            f"{recipient.id}: {exc}"
        )

        recipient.refresh_from_db()

        if recipient.status == "SENDING":

            recipient.status = "FAILED"

            recipient.failed_at = (
                timezone.now()
            )

            recipient.error_message = (
                str(exc)
            )

            recipient.save(
                update_fields=[
                    "status",
                    "failed_at",
                    "error_message",
                    "updated_at",
                ]
            )

            broadcast_campaign_update(
                campaign.id,
                recipient.id,
            )

        raise


# ============================================================
# Queue Campaign
# ============================================================

@shared_task(
    bind=True,
)
def queue_campaign(
    self,
    campaign_id: int,
):
    """
    Start processing a campaign through the global dispatcher.
    """

    try:

        campaign = (
            Campaign.objects
            .get(
                id=campaign_id,
            )
        )

    except Campaign.DoesNotExist:

        return {
            "success": False,
            "campaign_id": campaign_id,
            "status": "NOT_FOUND",
            "queued": 0,
        }

    # --------------------------------------------------------
    # Campaign must be RUNNING
    # --------------------------------------------------------

    if campaign.status != "RUNNING":

        return {
            "success": False,
            "campaign_id": campaign.id,
            "status": campaign.status,
            "queued": 0,
            "message": (
                "Campaign is not RUNNING."
            ),
        }

    # --------------------------------------------------------
    # Find pending recipients
    # --------------------------------------------------------

    recipients = (
        CampaignRecipient.objects
        .filter(
            campaign=campaign,
            status="PENDING",
        )
        .order_by("id")
    )

    queued = recipients.count()

    # --------------------------------------------------------
    # Start global dispatcher
    # --------------------------------------------------------

    if queued > 0:

        dispatch_next_recipient.delay()

    print(
        f"Campaign {campaign.id}: "
        f"{queued} recipients available for "
        "global dispatcher."
    )

    return {
        "success": True,
        "campaign_id": campaign.id,
        "status": campaign.status,
        "queued": queued,
    }


# ============================================================
# Global Dispatcher
# ============================================================

@shared_task
def dispatch_next_recipient():
    """
    Dispatch exactly one recipient.

    get_next_recipient() atomically changes:

        PENDING → QUEUED

    before the send task is created.

    Therefore the same recipient cannot be selected again
    by the next dispatcher invocation.
    """

    recipient = get_next_recipient()

    # --------------------------------------------------------
    # Nothing pending
    # --------------------------------------------------------

    if recipient is None:

        print(
            "Global dispatcher: "
            "no pending recipients."
        )

        return {
            "success": True,
            "status": "IDLE",
            "message": "No pending recipients.",
        }

    # --------------------------------------------------------
    # Dispatch one recipient
    # --------------------------------------------------------

    print(
        "Global dispatcher selected "
        f"recipient {recipient.id} "
        f"from campaign {recipient.campaign_id}."
    )

    send_campaign_recipient_task.delay(
        recipient.id
    )

    # --------------------------------------------------------
    # Schedule dispatcher again
    # --------------------------------------------------------

    dispatch_next_recipient.apply_async(
        countdown=1
    )

    return {
        "success": True,
        "status": "DISPATCHED",
        "recipient_id": recipient.id,
        "campaign_id": recipient.campaign_id,
    }

# ============================================================
# Generic Outbound WhatsApp Message
# ============================================================

@shared_task(
    bind=True,
    max_retries=3,
)
def send_message_task(
    self,
    message_id: int,
):
    """
    Send one generic outbound WhatsApp message.

    This task is used by:
        - Chat
        - Future automation
        - Future ERP integrations
        - Future scheduled messaging

    Campaign sending continues using the existing
    campaign-specific dispatcher for now.
    """

    result = send_outbound_message(
        message_id
    )

    # ---------------------------------------------------------
    # Message scheduled for a future global slot
    # ---------------------------------------------------------

    if (
        result.get("status")
        == "SCHEDULED"
    ):

        delay = result.get(
            "delay",
            0,
        )

        send_message_task.apply_async(
            args=[
                message_id,
            ],
            countdown=delay,
        )

        return result

    return result

@shared_task(bind=True, max_retries=3)
def process_webhook_task(self, payload: dict):
    """
    Process a WhatsApp webhook payload asynchronously.

    The webhook HTTP request only queues this task.
    Actual database processing happens inside Celery.
    """
    process_whatsapp_webhook(payload)

    return {
        "success": True,
        "status": "PROCESSED",
    }