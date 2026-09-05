import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..models import Conversation, Message
from ..tasks import send_message_task


def serialize_message(message):
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "customer_id": message.conversation.customer_id,
        "whatsapp_message_id": (
            message.whatsapp_message_id
        ),
        "direction": message.direction,
        "message_type": message.message_type,
        "text": message.text,
        "status": message.status,
        "created_at": (
            message.created_at.isoformat()
            if message.created_at
            else None
        ),
    }


@csrf_exempt
def send_conversation_message(
    request,
    conversation_id,
):
    """
    Queue a text message for a WhatsApp conversation.

    Important:

        This endpoint DOES NOT call WhatsApp Cloud API.

        It creates a QUEUED Message and hands
        execution to Celery.
    """

    # ---------------------------------------------------------
    # Method
    # ---------------------------------------------------------

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": (
                        "Only POST method is allowed."
                    ),
                    "details": {},
                },
            },
            status=405,
        )

    # ---------------------------------------------------------
    # Get conversation
    # ---------------------------------------------------------

    try:

        conversation = (
            Conversation.objects
            .select_related(
                "customer",
                "phone_number",
            )
            .get(
                id=conversation_id,
            )
        )

    except Conversation.DoesNotExist:

        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "CONVERSATION_NOT_FOUND",
                    "message": (
                        "Conversation not found."
                    ),
                    "details": {
                        "conversation_id": (
                            conversation_id
                        ),
                    },
                },
            },
            status=404,
        )

    # ---------------------------------------------------------
    # Parse JSON
    # ---------------------------------------------------------

    try:

        data = json.loads(
            request.body.decode("utf-8")
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):

        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "INVALID_JSON",
                    "message": (
                        "Request body must contain "
                        "valid JSON."
                    ),
                    "details": {},
                },
            },
            status=400,
        )

    # ---------------------------------------------------------
    # Validate message
    # ---------------------------------------------------------

    message_text = data.get(
        "message"
    )

    if not isinstance(
        message_text,
        str,
    ):

        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": (
                        "Message is required."
                    ),
                    "details": {
                        "field": "message",
                    },
                },
            },
            status=400,
        )

    message_text = message_text.strip()

    if not message_text:

        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": (
                        "Message cannot be empty."
                    ),
                    "details": {
                        "field": "message",
                    },
                },
            },
            status=400,
        )

    # ---------------------------------------------------------
    # Customer phone
    # ---------------------------------------------------------

    customer = conversation.customer

    if not customer.phone:

        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": (
                        "CUSTOMER_PHONE_MISSING"
                    ),
                    "message": (
                        "Customer does not have "
                        "a phone number."
                    ),
                    "details": {
                        "customer_id": (
                            customer.id
                        ),
                    },
                },
            },
            status=400,
        )

    # =========================================================
    # CREATE QUEUED MESSAGE
    # =========================================================

    message = Message.objects.create(
        conversation=conversation,
        direction="outbound",
        message_type="text",
        text=message_text,
        status="queued",
    )

    # ---------------------------------------------------------
    # Update conversation immediately
    # ---------------------------------------------------------

    from django.utils import timezone

    conversation.last_message_at = (
        timezone.now()
    )

    conversation.save(
        update_fields=[
            "last_message_at",
            "updated_at",
        ]
    )

    # =========================================================
    # SEND TO CELERY
    # =========================================================

    send_message_task.delay(
        message.id
    )

    # =========================================================
    # RESPONSE
    # =========================================================

    return JsonResponse(
        {
            "success": True,
            "data": {
                "message": (
                    serialize_message(
                        message
                    )
                ),
            },
            "message": (
                "WhatsApp message queued "
                "successfully."
            ),
            "meta": {
                "queued": True,
            },
        },
        status=202,
    )