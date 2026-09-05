import json

from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..models import Conversation, Message


# ============================================================
# Serializers
# ============================================================

def serialize_conversation(conversation):
    """
    Serialize a conversation for API responses.
    """

    unread_count = conversation.messages.filter(
        direction="inbound",
        status="received",
    ).count()

    last_message = (
        conversation.messages
        .order_by("-created_at")
        .first()
    )

    return {
        "id": conversation.id,

        "customer": {
            "id": conversation.customer.id,
            "name": conversation.customer.name,
            "phone": conversation.customer.phone,
            "whatsapp_id": conversation.customer.whatsapp_id,
        },

        "phone_number": {
            "id": conversation.phone_number.id,
            "display_name": conversation.phone_number.display_name,
            "phone_number": conversation.phone_number.phone_number,
            "phone_number_id": conversation.phone_number.phone_number_id,
        },

        "status": conversation.status,

        "last_message_at": (
            conversation.last_message_at.isoformat()
            if conversation.last_message_at
            else None
        ),

        "last_message": (
            serialize_message(last_message)
            if last_message
            else None
        ),

        "unread_count": unread_count,

        "created_at": (
            conversation.created_at.isoformat()
            if conversation.created_at
            else None
        ),

        "updated_at": (
            conversation.updated_at.isoformat()
            if conversation.updated_at
            else None
        ),
    }


def serialize_message(message):
    """
    Serialize one message.
    """

    if not message:
        return None

    return {
        "id": message.id,
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
# Conversation List
# ============================================================

@csrf_exempt
def conversation_list(request):
    """
    GET  -> List conversations
    POST -> Create conversation
    """

    if request.method == "POST":
        return conversation_create(request)

    if request.method != "GET":
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "Only GET and POST methods are allowed.",
                    "details": {},
                },
            },
            status=405,
        )

    try:
        conversations = (
            Conversation.objects
            .select_related(
                "customer",
                "phone_number",
            )
            .all()
        )

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        search = request.GET.get(
            "search",
            "",
        ).strip()

        if search:
            conversations = conversations.filter(
                Q(customer__name__icontains=search)
                | Q(customer__phone__icontains=search)
                | Q(customer__whatsapp_id__icontains=search)
            )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status = request.GET.get(
            "status",
            "",
        ).strip().lower()

        if status:

            if status not in {
                "open",
                "closed",
            }:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Status must be open or closed.",
                            "details": {
                                "field": "status",
                            },
                        },
                    },
                    status=400,
                )

            conversations = conversations.filter(
                status=status
            )

        # ----------------------------------------------------
        # Customer
        # ----------------------------------------------------

        customer_id = request.GET.get(
            "customer_id",
            "",
        ).strip()

        if customer_id:

            try:
                customer_id = int(customer_id)

            except ValueError:
                return JsonResponse(
                    {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "customer_id must be an integer.",
                            "details": {
                                "field": "customer_id",
                            },
                        },
                    },
                    status=400,
                )

            conversations = conversations.filter(
                customer_id=customer_id
            )

        # ----------------------------------------------------
        # Ordering
        # ----------------------------------------------------

        ordering = request.GET.get(
            "ordering",
            "-last_message_at",
        ).strip()

        allowed_ordering = {
            "id",
            "-id",
            "last_message_at",
            "-last_message_at",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        }

        if ordering not in allowed_ordering:
            ordering = "-last_message_at"

        conversations = conversations.order_by(
            ordering
        )

        # ----------------------------------------------------
        # Serialize
        # ----------------------------------------------------

        data = [
            serialize_conversation(conversation)
            for conversation in conversations
        ]

        return JsonResponse(
            {
                "success": True,
                "data": data,
                "message": "Conversations retrieved successfully.",
                "meta": {
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
                    "message": "Unable to retrieve conversations.",
                    "details": {},
                },
            },
            status=500,
        )


# ============================================================
# Conversation Detail
# ============================================================

@csrf_exempt
def conversation_detail(
    request,
    conversation_id,
):
    """
    GET   -> Retrieve conversation
    PATCH -> Update conversation
    """

    try:
        conversation = (
            Conversation.objects
            .select_related(
                "customer",
                "phone_number",
            )
            .get(
                id=conversation_id
            )
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

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return JsonResponse(
            {
                "success": True,
                "data": serialize_conversation(
                    conversation
                ),
                "message": "Conversation retrieved successfully.",
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

            # ------------------------------------------------
            # Allowed fields
            # ------------------------------------------------

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

                if status not in {
                    "open",
                    "closed",
                }:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "Status must be open or closed.",
                                "details": {
                                    "field": "status",
                                    "allowed_values": [
                                        "open",
                                        "closed",
                                    ],
                                },
                            },
                        },
                        status=400,
                    )

                conversation.status = status

            # ------------------------------------------------
            # Save
            # ------------------------------------------------

            with transaction.atomic():
                conversation.save()

            return JsonResponse(
                {
                    "success": True,
                    "data": serialize_conversation(
                        conversation
                    ),
                    "message": "Conversation updated successfully.",
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
                        "message": "Unable to update conversation.",
                        "details": {},
                    },
                },
                status=500,
            )

    # ========================================================
    # Unsupported Method
    # ========================================================

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
# Conversation Create
# ============================================================

@csrf_exempt
def conversation_create(request):

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

        customer_id = payload.get(
            "customer_id"
        )

        phone_number_id = payload.get(
            "phone_number_id"
        )

        if not customer_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "customer_id is required.",
                        "details": {
                            "field": "customer_id",
                        },
                    },
                },
                status=400,
            )

        if not phone_number_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "phone_number_id is required.",
                        "details": {
                            "field": "phone_number_id",
                        },
                    },
                },
                status=400,
            )

        # ----------------------------------------------------
        # Validate IDs
        # ----------------------------------------------------

        try:
            customer_id = int(customer_id)
            phone_number_id = int(phone_number_id)

        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "customer_id and phone_number_id must be integers.",
                        "details": {},
                    },
                },
                status=400,
            )

        # ----------------------------------------------------
        # Import models here to keep this module clean
        # ----------------------------------------------------

        from ..models import Customer, WhatsAppPhoneNumber

        try:
            customer = Customer.objects.get(
                id=customer_id
            )

        except Customer.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Customer not found.",
                        "details": {},
                    },
                },
                status=404,
            )

        try:
            phone_number = WhatsAppPhoneNumber.objects.get(
                id=phone_number_id
            )

        except WhatsAppPhoneNumber.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "WhatsApp phone number not found.",
                        "details": {},
                    },
                },
                status=404,
            )

        # ----------------------------------------------------
        # Check existing open conversation
        # ----------------------------------------------------

        existing = (
            Conversation.objects
            .filter(
                customer=customer,
                phone_number=phone_number,
                status="open",
            )
            .first()
        )

        if existing:

            return JsonResponse(
                {
                    "success": True,
                    "data": serialize_conversation(
                        existing
                    ),
                    "message": "An open conversation already exists.",
                    "meta": {
                        "existing": True,
                    },
                },
                status=200,
            )

        # ----------------------------------------------------
        # Create
        # ----------------------------------------------------

        with transaction.atomic():

            conversation = Conversation.objects.create(
                customer=customer,
                phone_number=phone_number,
                status="open",
            )

        return JsonResponse(
            {
                "success": True,
                "data": serialize_conversation(
                    conversation
                ),
                "message": "Conversation created successfully.",
                "meta": {
                    "existing": False,
                },
            },
            status=201,
        )

    except Exception:
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to create conversation.",
                    "details": {},
                },
            },
            status=500,
        )


# ============================================================
# Conversation Messages
# ============================================================

@csrf_exempt
def conversation_messages(
    request,
    conversation_id,
):

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

        data = [
            serialize_message(message)
            for message in messages
        ]

        return JsonResponse(
            {
                "success": True,
                "data": data,
                "message": "Conversation messages retrieved successfully.",
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
                    "message": "Unable to retrieve conversation messages.",
                    "details": {},
                },
            },
            status=500,
        )