import json

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..models import Conversation, Message


# ============================================================
# Message Serializer
# ============================================================

def serialize_message(message):
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "whatsapp_message_id": message.whatsapp_message_id,
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


# ============================================================
# Message List
# ============================================================

@csrf_exempt
def message_list(request, conversation_id):

    if request.method != "GET":
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "Only GET method is allowed.",
                    "details": {},
                },
            },
            status=405,
        )

    try:
        conversation = Conversation.objects.get(
            id=conversation_id
        )

    except Conversation.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Conversation not found.",
                    "details": {},
                },
            },
            status=404,
        )

    try:

        messages = (
            Message.objects
            .filter(
                conversation=conversation
            )
            .order_by("created_at")
        )

        # ----------------------------------------------------
        # Optional status filter
        # ----------------------------------------------------

        status = request.GET.get(
            "status",
            "",
        ).strip().lower()

        if status:

            allowed_statuses = {
                "received",
                "sent",
                "delivered",
                "read",
                "failed",
            }

            if status not in allowed_statuses:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid message status.",
                            "details": {
                                "field": "status",
                                "allowed_values": sorted(
                                    allowed_statuses
                                ),
                            },
                        },
                    },
                    status=400,
                )

            messages = messages.filter(
                status=status
            )

        # ----------------------------------------------------
        # Optional direction filter
        # ----------------------------------------------------

        direction = request.GET.get(
            "direction",
            "",
        ).strip().lower()

        if direction:

            if direction not in {
                "inbound",
                "outbound",
            }:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Direction must be inbound or outbound.",
                            "details": {
                                "field": "direction",
                            },
                        },
                    },
                    status=400,
                )

            messages = messages.filter(
                direction=direction
            )

        data = [
            serialize_message(message)
            for message in messages
        ]

        return JsonResponse(
            {
                "success": True,
                "data": data,
                "message": "Messages retrieved successfully.",
                "meta": {
                    "conversation_id": conversation.id,
                    "total": len(data),
                },
            },
            status=200,
        )

    except Exception:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to retrieve messages.",
                    "details": {},
                },
            },
            status=500,
        )


# ============================================================
# Message Detail
# ============================================================

@csrf_exempt
def message_detail(
    request,
    message_id,
):

    try:
        message = (
            Message.objects
            .select_related("conversation")
            .get(id=message_id)
        )

    except Message.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Message not found.",
                    "details": {},
                },
            },
            status=404,
        )

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return JsonResponse(
            {
                "success": True,
                "data": serialize_message(message),
                "message": "Message retrieved successfully.",
                "meta": {},
            },
            status=200,
        )

    # ========================================================
    # PATCH
    # ========================================================

    if request.method == "PATCH":

        try:

            try:
                payload = json.loads(
                    request.body or "{}"
                )

            except json.JSONDecodeError:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Request body must contain valid JSON.",
                            "details": {},
                        },
                    },
                    status=400,
                )

            if not isinstance(payload, dict):
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Request body must be a JSON object.",
                            "details": {},
                        },
                    },
                    status=400,
                )

            allowed_fields = {
                "status",
            }

            unknown_fields = (
                set(payload.keys())
                - allowed_fields
            )

            if unknown_fields:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "One or more fields are not allowed.",
                            "details": {
                                "fields": sorted(
                                    unknown_fields
                                ),
                            },
                        },
                    },
                    status=400,
                )

            # ------------------------------------------------
            # Status
            # ------------------------------------------------

            if "status" in payload:

                status = str(
                    payload["status"]
                ).strip().lower()

                allowed_statuses = {
                    "received",
                    "sent",
                    "delivered",
                    "read",
                    "failed",
                }

                if status not in allowed_statuses:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "Invalid message status.",
                                "details": {
                                    "field": "status",
                                    "allowed_values": sorted(
                                        allowed_statuses
                                    ),
                                },
                            },
                        },
                        status=400,
                    )

                message.status = status

            with transaction.atomic():
                message.save()

            return JsonResponse(
                {
                    "success": True,
                    "data": serialize_message(message),
                    "message": "Message updated successfully.",
                    "meta": {},
                },
                status=200,
            )

        except Exception:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Unable to update message.",
                        "details": {},
                    },
                },
                status=500,
            )

    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "Only GET and PATCH methods are allowed.",
                "details": {},
            },
        },
        status=405,
    )


# ============================================================
# Create Message
# ============================================================

@csrf_exempt
def message_create(
    request,
    conversation_id,
):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "Only POST method is allowed.",
                    "details": {},
                },
            },
            status=405,
        )

    try:

        # ----------------------------------------------------
        # Conversation
        # ----------------------------------------------------

        try:
            conversation = Conversation.objects.get(
                id=conversation_id
            )

        except Conversation.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Conversation not found.",
                        "details": {},
                    },
                },
                status=404,
            )

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:
            payload = json.loads(
                request.body or "{}"
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request body must contain valid JSON.",
                        "details": {},
                    },
                },
                status=400,
            )

        if not isinstance(payload, dict):
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request body must be a JSON object.",
                        "details": {},
                    },
                },
                status=400,
            )

        # ----------------------------------------------------
        # Allowed fields
        # ----------------------------------------------------

        allowed_fields = {
            "direction",
            "message_type",
            "text",
            "status",
            "whatsapp_message_id",
            "raw_payload",
        }

        unknown_fields = (
            set(payload.keys())
            - allowed_fields
        )

        if unknown_fields:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "One or more fields are not allowed.",
                        "details": {
                            "fields": sorted(
                                unknown_fields
                            ),
                        },
                    },
                },
                status=400,
            )

        # ----------------------------------------------------
        # Direction
        # ----------------------------------------------------

        direction = str(
            payload.get(
                "direction",
                "inbound",
            )
        ).strip().lower()

        if direction not in {
            "inbound",
            "outbound",
        }:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Direction must be inbound or outbound.",
                        "details": {
                            "field": "direction",
                        },
                    },
                },
                status=400,
            )

        # ----------------------------------------------------
        # Message Type
        # ----------------------------------------------------

        message_type = str(
            payload.get(
                "message_type",
                "text",
            )
        ).strip().lower()

        allowed_types = {
            "text",
            "image",
            "video",
            "audio",
            "document",
            "interactive",
            "template",
            "unknown",
        }

        if message_type not in allowed_types:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid message type.",
                        "details": {
                            "field": "message_type",
                            "allowed_values": sorted(
                                allowed_types
                            ),
                        },
                    },
                },
                status=400,
            )

        # ----------------------------------------------------
        # Text
        # ----------------------------------------------------

        text = str(
            payload.get(
                "text",
                "",
            )
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status = str(
            payload.get(
                "status",
                "received",
            )
        ).strip().lower()

        allowed_statuses = {
            "received",
            "sent",
            "delivered",
            "read",
            "failed",
        }

        if status not in allowed_statuses:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid message status.",
                        "details": {
                            "field": "status",
                            "allowed_values": sorted(
                                allowed_statuses
                            ),
                        },
                    },
                },
                status=400,
            )

        # ----------------------------------------------------
        # WhatsApp Message ID
        # ----------------------------------------------------

        whatsapp_message_id = (
            str(
                payload.get(
                    "whatsapp_message_id",
                    "",
                )
            ).strip()
            or None
        )

        # ----------------------------------------------------
        # Raw Payload
        # ----------------------------------------------------

        raw_payload = payload.get(
            "raw_payload",
            None,
        )

        if (
            raw_payload is not None
            and not isinstance(
                raw_payload,
                dict,
            )
        ):
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "raw_payload must be an object.",
                        "details": {
                            "field": "raw_payload",
                        },
                    },
                },
                status=400,
            )

        # ----------------------------------------------------
        # Create
        # ----------------------------------------------------

        with transaction.atomic():

            message = Message.objects.create(
                conversation=conversation,
                whatsapp_message_id=(
                    whatsapp_message_id
                ),
                direction=direction,
                message_type=message_type,
                text=text,
                status=status,
                raw_payload=raw_payload,
            )

            # Keep conversation activity updated
            conversation.last_message_at = (
                message.created_at
            )

            conversation.save(
                update_fields=[
                    "last_message_at",
                    "updated_at",
                ]
            )

        return JsonResponse(
            {
                "success": True,
                "data": serialize_message(
                    message
                ),
                "message": "Message created successfully.",
                "meta": {},
            },
            status=201,
        )

    except IntegrityError:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "DUPLICATE_MESSAGE",
                    "message": "A message with this WhatsApp message ID already exists.",
                    "details": {},
                },
            },
            status=409,
        )

    except Exception:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to create message.",
                    "details": {},
                },
            },
            status=500,
        )