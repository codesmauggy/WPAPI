import json

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..models import Audience, AudienceMember, Customer

from ..events import (
    broadcast_audience_created,
    broadcast_audience_updated,
    broadcast_audience_deleted,
    broadcast_audience_membership_updated,
)


# ============================================================
# Customer Serializer
# ============================================================

def serialize_audience_customer(customer):
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
        "is_active": customer.is_active,
        "status": customer.status,
    }


# ============================================================
# Audience Serializer
# ============================================================

def serialize_audience(audience):
    return {
        "id": audience.id,
        "name": audience.name,
        "description": audience.description,
        "is_active": audience.is_active,
        "member_count": audience.members.count(),
        "created_at": (
            audience.created_at.isoformat()
            if audience.created_at
            else None
        ),
        "updated_at": (
            audience.updated_at.isoformat()
            if audience.updated_at
            else None
        ),
    }


# ============================================================
# Audience Member Serializer
# ============================================================

def serialize_audience_member(member):
    return {
        "id": member.id,
        "audience_id": member.audience_id,
        "customer": serialize_audience_customer(
            member.customer
        ),
        "created_at": (
            member.created_at.isoformat()
            if member.created_at
            else None
        ),
    }


# ============================================================
# Helpers
# ============================================================

def json_error(
    code,
    message,
    status=400,
    details=None,
):
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        },
        status=status,
    )


def parse_json_body(request):
    try:
        payload = json.loads(
            request.body or "{}"
        )
    except json.JSONDecodeError:
        return None, json_error(
            "VALIDATION_ERROR",
            "Request body must contain valid JSON.",
            400,
        )

    if not isinstance(payload, dict):
        return None, json_error(
            "VALIDATION_ERROR",
            "Request body must be a JSON object.",
            400,
        )

    return payload, None


# ============================================================
# Audience List / Create
# ============================================================

@csrf_exempt
def audience_list(request):

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        try:
            audiences = Audience.objects.all()

            # ------------------------------------------------
            # Search
            # ------------------------------------------------

            search = request.GET.get(
                "search",
                "",
            ).strip()

            if search:
                audiences = audiences.filter(
                    Q(name__icontains=search)
                    | Q(description__icontains=search)
                )

            # ------------------------------------------------
            # Active
            # ------------------------------------------------

            is_active = request.GET.get(
                "is_active",
                "",
            ).strip().lower()

            if is_active in {
                "true",
                "1",
                "yes",
            }:
                audiences = audiences.filter(
                    is_active=True
                )

            elif is_active in {
                "false",
                "0",
                "no",
            }:
                audiences = audiences.filter(
                    is_active=False
                )

            # ------------------------------------------------
            # Ordering
            # ------------------------------------------------

            ordering = request.GET.get(
                "ordering",
                "-created_at",
            ).strip()

            allowed_ordering = {
                "id",
                "-id",
                "name",
                "-name",
                "created_at",
                "-created_at",
                "updated_at",
                "-updated_at",
            }

            if ordering not in allowed_ordering:
                ordering = "-created_at"

            audiences = audiences.order_by(
                ordering
            )

            data = [
                serialize_audience(audience)
                for audience in audiences
            ]

            return JsonResponse(
                {
                    "success": True,
                    "data": data,
                    "message": (
                        "Audiences retrieved successfully."
                    ),
                    "meta": {
                        "total": len(data),
                    },
                },
                status=200,
            )

        except Exception:
            return json_error(
                "INTERNAL_ERROR",
                "Unable to retrieve audiences.",
                500,
            )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        payload, error = parse_json_body(
            request
        )

        if error:
            return error

        name = str(
            payload.get("name", "")
        ).strip()

        description = str(
            payload.get("description", "")
        ).strip()

        is_active = payload.get(
            "is_active",
            True,
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not name:
            return json_error(
                "VALIDATION_ERROR",
                "Audience name is required.",
                400,
                {
                    "field": "name",
                },
            )

        if len(name) > 255:
            return json_error(
                "VALIDATION_ERROR",
                "Audience name cannot exceed 255 characters.",
                400,
                {
                    "field": "name",
                },
            )

        if not isinstance(
            is_active,
            bool,
        ):
            return json_error(
                "VALIDATION_ERROR",
                "is_active must be a boolean.",
                400,
                {
                    "field": "is_active",
                },
            )

        try:

            with transaction.atomic():
                audience = Audience.objects.create(
                    name=name,
                    description=description,
                    is_active=is_active,
                )

                transaction.on_commit(
                    lambda: broadcast_audience_created(
                        audience
                    )
                )

            return JsonResponse(
                {
                    "success": True,
                    "data": serialize_audience(
                        audience
                    ),
                    "message": (
                        "Audience created successfully."
                    ),
                    "meta": {},
                },
                status=201,
            )

        except IntegrityError:
            return json_error(
                "AUDIENCE_CREATE_FAILED",
                "Unable to create audience.",
                409,
            )

        except Exception:
            return json_error(
                "INTERNAL_ERROR",
                "Unable to create audience.",
                500,
            )

    # ========================================================
    # Unsupported Method
    # ========================================================

    return json_error(
        "METHOD_NOT_ALLOWED",
        "Only GET and POST methods are allowed.",
        405,
    )


# ============================================================
# Audience Detail / Update / Delete
# ============================================================

@csrf_exempt
def audience_detail(
    request,
    audience_id,
):

    try:
        audience = Audience.objects.get(
            id=audience_id
        )

    except Audience.DoesNotExist:
        return json_error(
            "AUDIENCE_NOT_FOUND",
            "Audience not found.",
            404,
        )

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return JsonResponse(
            {
                "success": True,
                "data": serialize_audience(
                    audience
                ),
                "message": (
                    "Audience retrieved successfully."
                ),
                "meta": {},
            },
            status=200,
        )

    # ========================================================
    # PATCH
    # ========================================================

    if request.method == "PATCH":

        payload, error = parse_json_body(
            request
        )

        if error:
            return error

        allowed_fields = {
            "name",
            "description",
            "is_active",
        }

        unknown_fields = (
            set(payload.keys())
            - allowed_fields
        )

        if unknown_fields:
            return json_error(
                "VALIDATION_ERROR",
                "One or more fields are not allowed.",
                400,
                {
                    "fields": sorted(
                        unknown_fields
                    ),
                },
            )

        # ----------------------------------------------------
        # Name
        # ----------------------------------------------------

        if "name" in payload:

            name = str(
                payload["name"]
            ).strip()

            if not name:
                return json_error(
                    "VALIDATION_ERROR",
                    "Audience name cannot be empty.",
                    400,
                    {
                        "field": "name",
                    },
                )

            if len(name) > 255:
                return json_error(
                    "VALIDATION_ERROR",
                    "Audience name cannot exceed 255 characters.",
                    400,
                    {
                        "field": "name",
                    },
                )

            audience.name = name

        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        if "description" in payload:

            audience.description = str(
                payload["description"]
            ).strip()

        # ----------------------------------------------------
        # Active
        # ----------------------------------------------------

        if "is_active" in payload:

            if not isinstance(
                payload["is_active"],
                bool,
            ):
                return json_error(
                    "VALIDATION_ERROR",
                    "is_active must be a boolean.",
                    400,
                    {
                        "field": "is_active",
                    },
                )

            audience.is_active = (
                payload["is_active"]
            )

        try:

            with transaction.atomic():
                audience.save()

                transaction.on_commit(
                    lambda: broadcast_audience_updated(
                        audience
                    )
                )

            return JsonResponse(
                {
                    "success": True,
                    "data": serialize_audience(
                        audience
                    ),
                    "message": (
                        "Audience updated successfully."
                    ),
                    "meta": {},
                },
                status=200,
            )

        except Exception:
            return json_error(
                "INTERNAL_ERROR",
                "Unable to update audience.",
                500,
            )

    # ========================================================
    # DELETE
    # ========================================================

    if request.method == "DELETE":
        try:
            audience_id_value = audience.id
            audience_name_value = audience.name

            with transaction.atomic():
                audience.delete()

                transaction.on_commit(
                    lambda: broadcast_audience_deleted(
                        audience_id_value,
                        audience_name_value,
                    )
                )

            return JsonResponse(
                {
                    "success": True,
                    "data": None,
                    "message": (
                        "Audience deleted successfully."
                    ),
                    "meta": {},
                },
                status=200,
            )

        except ProtectedError:

            return json_error(
                "AUDIENCE_IN_USE",
                (
                    "This audience cannot be deleted "
                    "because it is used by one or more campaigns."
                ),
                409,
            )

        except Exception:
            return json_error(
                "INTERNAL_ERROR",
                "Unable to delete audience.",
                500,
            )

    # ========================================================
    # Unsupported
    # ========================================================

    return json_error(
        "METHOD_NOT_ALLOWED",
        "Only GET, PATCH and DELETE methods are allowed.",
        405,
    )


# ============================================================
# Audience Members
# ============================================================

@csrf_exempt
def audience_members(
    request,
    audience_id,
):

    try:
        audience = Audience.objects.get(
            id=audience_id
        )

    except Audience.DoesNotExist:
        return json_error(
            "AUDIENCE_NOT_FOUND",
            "Audience not found.",
            404,
        )

    # ========================================================
    # GET MEMBERS
    # ========================================================

    if request.method == "GET":

        try:

            members = (
                AudienceMember.objects
                .filter(
                    audience=audience
                )
                .select_related("customer")
                .order_by("-created_at")
            )

            search = request.GET.get(
                "search",
                "",
            ).strip()

            if search:

                members = members.filter(
                    Q(customer__name__icontains=search)
                    | Q(customer__phone__icontains=search)
                    | Q(
                        customer__whatsapp_id__icontains=search
                    )
                )

            data = [
                serialize_audience_member(member)
                for member in members
            ]

            return JsonResponse(
                {
                    "success": True,
                    "data": data,
                    "message": (
                        "Audience members retrieved successfully."
                    ),
                    "meta": {
                        "total": len(data),
                        "member_count": (
                            audience.members.count()
                        ),
                    },
                },
                status=200,
            )

        except Exception:
            return json_error(
                "INTERNAL_ERROR",
                "Unable to retrieve audience members.",
                500,
            )

    # ========================================================
    # POST MEMBER
    # ========================================================

    if request.method == "POST":

        payload, error = parse_json_body(
            request
        )

        if error:
            return error

        customer_id = payload.get(
            "customer_id"
        )

        if customer_id is None:
            return json_error(
                "VALIDATION_ERROR",
                "customer_id is required.",
                400,
                {
                    "field": "customer_id",
                },
            )

        try:
            customer = Customer.objects.get(
                id=customer_id
            )

        except (
            Customer.DoesNotExist
        ):
            return json_error(
                "CUSTOMER_NOT_FOUND",
                "Customer not found.",
                404,
            )

        # ----------------------------------------------------
        # Duplicate protection
        # ----------------------------------------------------

        if AudienceMember.objects.filter(
            audience=audience,
            customer=customer,
        ).exists():

            return json_error(
                "DUPLICATE_MEMBER",
                "Customer is already a member of this audience.",
                409,
                {
                    "audience_id": audience.id,
                    "customer_id": customer.id,
                },
            )

        try:

            with transaction.atomic():
                member = (
                    AudienceMember.objects.create(
                        audience=audience,
                        customer=customer,
                    )
                )

                transaction.on_commit(
                    lambda: broadcast_audience_membership_updated(
                        audience,
                        "added",
                        customer=customer,
                    )
                )

            member = (
                AudienceMember.objects
                .select_related("customer")
                .get(id=member.id)
            )

            return JsonResponse(
                {
                    "success": True,
                    "data": serialize_audience_member(
                        member
                    ),
                    "message": (
                        "Customer added to audience successfully."
                    ),
                    "meta": {
                        "member_count": (
                            audience.members.count()
                        ),
                    },
                },
                status=201,
            )

        except IntegrityError:

            return json_error(
                "DUPLICATE_MEMBER",
                "Customer is already a member of this audience.",
                409,
            )

        except Exception:
            return json_error(
                "INTERNAL_ERROR",
                "Unable to add customer to audience.",
                500,
            )

    return json_error(
        "METHOD_NOT_ALLOWED",
        "Only GET and POST methods are allowed.",
        405,
    )


# ============================================================
# Remove Audience Member
# ============================================================

@csrf_exempt
def audience_member_detail(
    request,
    audience_id,
    customer_id,
):

    if request.method != "DELETE":
        return json_error(
            "METHOD_NOT_ALLOWED",
            "Only DELETE method is allowed.",
            405,
        )

    try:
        audience = Audience.objects.get(
            id=audience_id
        )

    except Audience.DoesNotExist:
        return json_error(
            "AUDIENCE_NOT_FOUND",
            "Audience not found.",
            404,
        )

    try:
        member = AudienceMember.objects.get(
            audience=audience,
            customer_id=customer_id,
        )

    except AudienceMember.DoesNotExist:
        return json_error(
            "MEMBER_NOT_FOUND",
            "Customer is not a member of this audience.",
            404,
        )

    try:

        customer_id_value = member.customer_id

        with transaction.atomic():
            member.delete()

            transaction.on_commit(
                lambda: broadcast_audience_membership_updated(
                    audience,
                    "removed",
                    customer_id=customer_id_value,
                )
            )

        return JsonResponse(
            {
                "success": True,
                "data": None,
                "message": (
                    "Customer removed from audience successfully."
                ),
                "meta": {
                    "member_count": (
                        audience.members.count()
                    ),
                },
            },
            status=200,
        )

    except Exception:
        return json_error(
            "INTERNAL_ERROR",
            "Unable to remove customer from audience.",
            500,
        )


# ============================================================
# Audience Customer Search
# ============================================================

@csrf_exempt
def audience_customers(
    request,
    audience_id,
):

    if request.method != "GET":
        return json_error(
            "METHOD_NOT_ALLOWED",
            "Only GET method is allowed.",
            405,
        )

    try:
        audience = Audience.objects.get(
            id=audience_id
        )

    except Audience.DoesNotExist:
        return json_error(
            "AUDIENCE_NOT_FOUND",
            "Audience not found.",
            404,
        )

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
                | Q(
                    whatsapp_id__icontains=search
                )
            )

        # ----------------------------------------------------
        # Active filter
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
        # Marketing opt-in filter
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
        # Exclude existing audience members
        # ----------------------------------------------------

        existing_customer_ids = AudienceMember.objects.filter(
            audience=audience
        ).values_list(
            "customer_id",
            flat=True,
        )

        customers = customers.exclude(
            id__in=existing_customer_ids
        )

        customers = customers.order_by(
            "name",
            "id",
        )

        data = [
            serialize_audience_customer(
                customer
            )
            for customer in customers
        ]

        return JsonResponse(
            {
                "success": True,
                "data": data,
                "message": (
                    "Audience customers retrieved successfully."
                ),
                "meta": {
                    "total": len(data),
                    "audience_id": audience.id,
                },
            },
            status=200,
        )

    except Exception:
        return json_error(
            "INTERNAL_ERROR",
            "Unable to retrieve audience customers.",
            500,
        )