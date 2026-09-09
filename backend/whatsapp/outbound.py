from django.db import transaction
from django.utils import timezone

from .models import Conversation, Message
from .rate_limiter import reserve_send_slot
from .services import send_text_message, WhatsAppAPIError
from .events import broadcast_dashboard_event


def serialize_message(message):
    """
    Serialize a Message instance into the standard API shape.
    """

    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "whatsapp_message_id": message.whatsapp_message_id,
        "direction": message.direction,
        "message_type": message.message_type,
        "text": message.text,
        "status": message.status,
        "read_at": (
            message.read_at.isoformat()
            if message.read_at
            else None
        ),
        "created_at": (
            message.created_at.isoformat()
            if message.created_at
            else None
        ),
    }


def claim_message_for_sending(message_id):
    """
    Atomically change QUEUED -> SENDING.

    Returns:
        Message instance if successfully claimed.
        None if the message is no longer queued.
    """

    with transaction.atomic():

        message = (
            Message.objects
            .select_for_update()
            .select_related(
                "conversation",
                "conversation__customer",
                "conversation__phone_number",
            )
            .filter(
                id=message_id,
                status="queued",
                direction="outbound",
            )
            .first()
        )

        if message is None:
            return None

        message.status = "sending"

        message.save(
            update_fields=[
                "status",
            ]
        )

        broadcast_dashboard_event(
            {
                "type": "message.updated",
                "conversation_id": message.conversation_id,
                "message": serialize_message(message),
            }
        )

        return message


def mark_message_failed(
    message_id,
    error,
):
    """
    Mark an outbound message as failed.
    """

    updated = (
        Message.objects
        .select_related("conversation")
        .filter(id=message_id)
        .update(
            status="failed",
            raw_payload={
                "error": str(error),
            },
        )
    )

    if updated:
        message = Message.objects.get(id=message_id)
        broadcast_dashboard_event(
            {
                "type": "message.updated",
                "conversation_id": message.conversation_id,
                "message": serialize_message(message),
            }
        )


def send_outbound_message(message_id):
    """
    Execute one queued outbound WhatsApp message.

    Flow:

        QUEUED
          ↓
        Redis global limiter
          ↓
        SENDING
          ↓
        WhatsApp Cloud API
          ↓
        SENT / FAILED
    """

    # ---------------------------------------------------------
    # Load message
    # ---------------------------------------------------------

    try:

        message = (
            Message.objects
            .select_related(
                "conversation",
                "conversation__customer",
                "conversation__phone_number",
            )
            .get(
                id=message_id,
            )
        )

    except Message.DoesNotExist:

        return {
            "success": False,
            "message_id": message_id,
            "status": "NOT_FOUND",
        }

    # ---------------------------------------------------------
    # Only queued outbound messages are eligible
    # ---------------------------------------------------------

    if message.direction != "outbound":

        return {
            "success": False,
            "message_id": message.id,
            "status": message.status,
            "message": (
                "Message is not an outbound message."
            ),
        }

    if message.status != "queued":

        return {
            "success": False,
            "message_id": message.id,
            "status": message.status,
            "message": (
                "Message is no longer queued."
            ),
        }

    # ---------------------------------------------------------
    # Customer phone
    # ---------------------------------------------------------

    customer = message.conversation.customer

    if not customer.phone:

        mark_message_failed(
            message.id,
            "Customer does not have a phone number.",
        )

        return {
            "success": False,
            "message_id": message.id,
            "status": "FAILED",
            "error": (
                "Customer does not have a phone number."
            ),
        }

    # =========================================================
    # GLOBAL REDIS RATE LIMITER
    # =========================================================

    delay = reserve_send_slot()

    if delay > 0:

        print(
            f"Outbound message {message.id} "
            f"scheduled in {delay:.2f} seconds."
        )

        return {
            "success": True,
            "message_id": message.id,
            "status": "SCHEDULED",
            "delay": delay,
        }

    # =========================================================
    # ATOMIC CLAIM
    # =========================================================

    message = claim_message_for_sending(
        message.id
    )

    if message is None:

        return {
            "success": False,
            "message_id": message_id,
            "status": "NOT_QUEUED",
            "message": (
                "Message was already processed."
            ),
        }

    customer = message.conversation.customer

    # =========================================================
    # SEND TO WHATSAPP
    # =========================================================

    try:

        result = send_text_message(
            recipient_phone=customer.phone,
            message=message.text,
        )

        # -----------------------------------------------------
        # Extract WhatsApp message ID
        # -----------------------------------------------------

        whatsapp_message_id = None

        messages = result.get(
            "messages",
            [],
        )

        if messages:

            whatsapp_message_id = (
                messages[0].get("id")
            )

        # -----------------------------------------------------
        # Update message
        # -----------------------------------------------------

        Message.objects.filter(
            id=message.id,
        ).update(
            whatsapp_message_id=(
                whatsapp_message_id
            ),
            status="sent",
            raw_payload=result,
        )

        message.refresh_from_db()

        broadcast_dashboard_event(
            {
                "type": "message.updated",
                "conversation_id": message.conversation_id,
                "message": serialize_message(message),
            }
        )

        # -----------------------------------------------------
        # Update conversation
        # -----------------------------------------------------

        conversation = (
            message.conversation
        )

        conversation.last_message_at = (
            timezone.now()
        )

        conversation.save(
            update_fields=[
                "last_message_at",
                "updated_at",
            ]
        )

        broadcast_dashboard_event(
            {
                "type": "conversation.updated",
                "conversation_id": conversation.id,
                "last_message_at": conversation.last_message_at.isoformat(),
                "last_message": serialize_message(message),
            }
        )

        print(
            f"Outbound message {message.id} "
            "sent successfully."
        )

        return {
            "success": True,
            "message_id": message.id,
            "status": "SENT",
            "whatsapp_message_id": (
                whatsapp_message_id
            ),
        }

    # =========================================================
    # WHATSAPP API FAILURE
    # =========================================================

    except WhatsAppAPIError as exc:

        mark_message_failed(
            message.id,
            exc,
        )

        print(
            f"Outbound message {message.id} "
            f"failed: {exc}"
        )

        return {
            "success": False,
            "message_id": message.id,
            "status": "FAILED",
            "error": str(exc),
        }

    # =========================================================
    # UNEXPECTED FAILURE
    # =========================================================

    except Exception as exc:

        mark_message_failed(
            message.id,
            exc,
        )

        print(
            f"Unexpected error sending "
            f"message {message.id}: {exc}"
        )

        raise