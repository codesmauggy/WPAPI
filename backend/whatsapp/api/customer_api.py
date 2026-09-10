import json

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q
from ..models import Customer
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from ..events import (
    broadcast_customer_created,
    broadcast_customer_updated,
)

# ============================================================
# Customer Serializer
# ============================================================

def serialize_customer(customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "whatsapp_id": customer.whatsapp_id,

        "marketing_opted_in": customer.marketing_opted_in,
        "marketing_opted_in_at": (
            customer.marketing_opted_in_at.isoformat()
            if customer.marketing_opted_in_at
            else None
        ),
        "marketing_opted_out_at": (
            customer.marketing_opted_out_at.isoformat()
            if customer.marketing_opted_out_at
            else None
        ),

        "tags": customer.tags,
        "custom_fields": customer.custom_fields,

        "last_message_at": (
            customer.last_message_at.isoformat()
            if customer.last_message_at
            else None
        ),

        "is_active": customer.is_active,
        "status": customer.status,

        "created_at": (
            customer.created_at.isoformat()
            if customer.created_at
            else None
        ),
        "updated_at": (
            customer.updated_at.isoformat()
            if customer.updated_at
            else None
        ),
    }


# ============================================================
# Customer List
# ============================================================

@csrf_exempt
def customer_list(request):
    if request.method == "POST":
        return customer_create(request)

    if request.method != "GET":
        return JsonResponse({
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "Method not allowed.",
                "details": {},
            },
        }, status=405)

    try:
        customers = Customer.objects.all()

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        search = request.GET.get(
            "search",
            "",
        ).strip()

        if search:
            customers = customers.filter(
                Q(name__icontains=search)
                | Q(phone__icontains=search)
                | Q(whatsapp_id__icontains=search)
            )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status = request.GET.get(
            "status",
            "",
        ).strip()

        if status:
            customers = customers.filter(
                status=status
            )

        # ----------------------------------------------------
        # Active
        # ----------------------------------------------------

        is_active = request.GET.get(
            "is_active",
            "",
        ).strip().lower()

        if is_active in {
            "true",
            "1",
            "yes",
        }:
            customers = customers.filter(
                is_active=True
            )

        elif is_active in {
            "false",
            "0",
            "no",
        }:
            customers = customers.filter(
                is_active=False
            )

        # ----------------------------------------------------
        # Marketing Opt-In
        # ----------------------------------------------------

        marketing_opted_in = request.GET.get(
            "marketing_opted_in",
            "",
        ).strip().lower()

        if marketing_opted_in in {
            "true",
            "1",
            "yes",
        }:
            customers = customers.filter(
                marketing_opted_in=True
            )

        elif marketing_opted_in in {
            "false",
            "0",
            "no",
        }:
            customers = customers.filter(
                marketing_opted_in=False
            )

        # ----------------------------------------------------
        # Ordering
        # ----------------------------------------------------

        ordering = request.GET.get(
            "ordering",
            "-created_at",
        ).strip()

        allowed_ordering = {
            "id",
            "-id",
            "name",
            "-name",
            "phone",
            "-phone",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
            "last_message_at",
            "-last_message_at",
        }

        if ordering not in allowed_ordering:
            ordering = "-created_at"

        customers = customers.order_by(
            ordering
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        data = [
            serialize_customer(customer)
            for customer in customers
        ]

        return JsonResponse(
            {
                "success": True,
                "data": data,
                "message": "Customers retrieved successfully.",
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
                    "message": "Unable to retrieve customers.",
                    "details": {},
                },
            },
            status=500,
        )


# ============================================================
# Customer Detail
# ============================================================

# @require_GET
# def customer_detail(
#     request,
#     customer_id,
# ):
#     """
#     Return one customer by ID.
#     """

#     try:
#         customer = Customer.objects.get(
#             id=customer_id
#         )

#     except Customer.DoesNotExist:
#         return JsonResponse(
#             {
#                 "success": False,
#                 "error": {
#                     "code": "NOT_FOUND",
#                     "message": "Customer not found.",
#                     "details": {},
#                 },
#             },
#             status=404,
#         )

#     except Exception:
#         return JsonResponse(
#             {
#                 "success": False,
#                 "error": {
#                     "code": "INTERNAL_ERROR",
#                     "message": "Unable to retrieve customer.",
#                     "details": {},
#                 },
#             },
#             status=500,
#         )

#     return JsonResponse(
#         {
#             "success": True,
#             "data": serialize_customer(
#                 customer
#             ),
#             "message": "Customer retrieved successfully.",
#             "meta": {},
#         },
#         status=200,
#     )

@csrf_exempt
@require_POST
def customer_create(request):
    try:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request body must contain valid JSON.",
                    "details": {},
                },
            }, status=400)

        name = str(payload.get("name", "")).strip()
        phone = str(payload.get("phone", "")).strip()
        whatsapp_id = str(payload.get("whatsapp_id", "")).strip() or None

        if not name:
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Name is required.",
                    "details": {
                        "field": "name",
                    },
                },
            }, status=400)

        if not phone:
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Phone is required.",
                    "details": {
                        "field": "phone",
                    },
                },
            }, status=400)

        # Check existing phone
        if Customer.objects.filter(phone=phone).exists():
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "DUPLICATE_CUSTOMER",
                    "message": "A customer with this phone number already exists.",
                    "details": {
                        "field": "phone",
                    },
                },
            }, status=409)

        # whatsapp_id is unique when provided
        if whatsapp_id and Customer.objects.filter(
            whatsapp_id=whatsapp_id
        ).exists():
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "DUPLICATE_CUSTOMER",
                    "message": "A customer with this WhatsApp ID already exists.",
                    "details": {
                        "field": "whatsapp_id",
                    },
                },
            }, status=409)

        marketing_opted_in = payload.get(
            "marketing_opted_in",
            False,
        )

        if not isinstance(marketing_opted_in, bool):
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "marketing_opted_in must be a boolean.",
                    "details": {
                        "field": "marketing_opted_in",
                    },
                },
            }, status=400)

        tags = payload.get("tags", [])
        custom_fields = payload.get("custom_fields", {})

        if not isinstance(tags, list):
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Tags must be an array.",
                    "details": {
                        "field": "tags",
                    },
                },
            }, status=400)

        if not isinstance(custom_fields, dict):
            return JsonResponse({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "custom_fields must be an object.",
                    "details": {
                        "field": "custom_fields",
                    },
                },
            }, status=400)

        with transaction.atomic():
            customer = Customer.objects.create(
                name=name,
                phone=phone,
                whatsapp_id=whatsapp_id,
                marketing_opted_in=marketing_opted_in,
                tags=tags,
                custom_fields=custom_fields,
            )

        transaction.on_commit(
            lambda: broadcast_customer_created(customer)
        )

        return JsonResponse({
            "success": True,
            "data": serialize_customer(customer),
            "message": "Customer created successfully.",
            "meta": {},
        }, status=201)

    except IntegrityError:
        return JsonResponse({
            "success": False,
            "error": {
                "code": "DUPLICATE_CUSTOMER",
                "message": "A customer with the provided unique value already exists.",
                "details": {},
            },
        }, status=409)

    except Exception:
        return JsonResponse({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Unable to create customer.",
                "details": {},
            },
        }, status=500)

# ============================================================
# Customer Detail / Update
# ============================================================

@csrf_exempt
def customer_detail(
    request,
    customer_id,
):
    """
    Retrieve or update one customer by ID.

    GET   -> Retrieve customer
    PATCH -> Update customer
    """

    # --------------------------------------------------------
    # Find customer
    # --------------------------------------------------------

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

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return JsonResponse(
            {
                "success": True,
                "data": serialize_customer(
                    customer
                ),
                "message": "Customer retrieved successfully.",
                "meta": {},
            },
            status=200,
        )

    # ========================================================
    # PATCH
    # ========================================================

    if request.method == "PATCH":

        try:

            # ------------------------------------------------
            # Parse JSON
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Validate payload
            # ------------------------------------------------

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
                "name",
                "phone",
                "whatsapp_id",
                "marketing_opted_in",
                "tags",
                "custom_fields",
                "is_active",
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

            # =================================================
            # Basic field validation
            # =================================================

            # -------------------------------------------------
            # Name
            # -------------------------------------------------

            if "name" in payload:

                name = str(
                    payload["name"]
                ).strip()

                if not name:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "Name cannot be empty.",
                                "details": {
                                    "field": "name",
                                },
                            },
                        },
                        status=400,
                    )

                customer.name = name

            # -------------------------------------------------
            # Phone
            # -------------------------------------------------

            if "phone" in payload:

                phone = str(
                    payload["phone"]
                ).strip()

                if not phone:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "Phone cannot be empty.",
                                "details": {
                                    "field": "phone",
                                },
                            },
                        },
                        status=400,
                    )

                if Customer.objects.filter(
                    phone=phone
                ).exclude(
                    id=customer.id
                ).exists():

                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "DUPLICATE_CUSTOMER",
                                "message": "A customer with this phone number already exists.",
                                "details": {
                                    "field": "phone",
                                },
                            },
                        },
                        status=409,
                    )

                customer.phone = phone

            # -------------------------------------------------
            # WhatsApp ID
            # -------------------------------------------------

            if "whatsapp_id" in payload:

                whatsapp_id = str(
                    payload["whatsapp_id"]
                ).strip() or None

                if (
                    whatsapp_id
                    and Customer.objects.filter(
                        whatsapp_id=whatsapp_id
                    )
                    .exclude(
                        id=customer.id
                    )
                    .exists()
                ):

                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "DUPLICATE_CUSTOMER",
                                "message": "A customer with this WhatsApp ID already exists.",
                                "details": {
                                    "field": "whatsapp_id",
                                },
                            },
                        },
                        status=409,
                    )

                customer.whatsapp_id = (
                    whatsapp_id
                )

            # -------------------------------------------------
            # Tags
            # -------------------------------------------------

            if "tags" in payload:

                if not isinstance(
                    payload["tags"],
                    list,
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "Tags must be an array.",
                                "details": {
                                    "field": "tags",
                                },
                            },
                        },
                        status=400,
                    )

                customer.tags = payload["tags"]

            # -------------------------------------------------
            # Custom Fields
            # -------------------------------------------------

            if "custom_fields" in payload:

                if not isinstance(
                    payload["custom_fields"],
                    dict,
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "custom_fields must be an object.",
                                "details": {
                                    "field": "custom_fields",
                                },
                            },
                        },
                        status=400,
                    )

                customer.custom_fields = (
                    payload["custom_fields"]
                )

            # -------------------------------------------------
            # Active
            # -------------------------------------------------

            if "is_active" in payload:

                if not isinstance(
                    payload["is_active"],
                    bool,
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "is_active must be a boolean.",
                                "details": {
                                    "field": "is_active",
                                },
                            },
                        },
                        status=400,
                    )

                customer.is_active = (
                    payload["is_active"]
                )

            # -------------------------------------------------
            # Status
            # -------------------------------------------------

            if "status" in payload:

                status = str(
                    payload["status"]
                ).strip()

                if not status:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "Status cannot be empty.",
                                "details": {
                                    "field": "status",
                                },
                            },
                        },
                        status=400,
                    )

                customer.status = status

            # =================================================
            # Marketing Opt-In / Opt-Out
            # =================================================

            if "marketing_opted_in" in payload:

                marketing_opted_in = (
                    payload[
                        "marketing_opted_in"
                    ]
                )

                if not isinstance(
                    marketing_opted_in,
                    bool,
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "marketing_opted_in must be a boolean.",
                                "details": {
                                    "field": "marketing_opted_in",
                                },
                            },
                        },
                        status=400,
                    )

                customer.marketing_opted_in = (
                    marketing_opted_in
                )

                if marketing_opted_in:

                    customer.marketing_opted_in_at = (
                        timezone.now()
                    )

                    customer.marketing_opted_out_at = (
                        None
                    )

                else:

                    customer.marketing_opted_out_at = (
                        timezone.now()
                    )

                    customer.marketing_opted_in_at = (
                        None
                    )

                # Keep legacy field synchronized
                customer.opt_in = (
                    marketing_opted_in
                )

            # =================================================
            # Save
            # =================================================

            with transaction.atomic():
                customer.save()

            transaction.on_commit(
                lambda: broadcast_customer_updated(customer)
            )

            return JsonResponse(
                {
                    "success": True,
                    "data": serialize_customer(
                        customer
                    ),
                    "message": "Customer updated successfully.",
                    "meta": {},
                },
                status=200,
            )

        except IntegrityError:

            return JsonResponse(
                {
                    "success": False,
                    "error": {
                        "code": "DUPLICATE_CUSTOMER",
                        "message": "A customer with the provided unique value already exists.",
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
                        "message": "Unable to update customer.",
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