import csv
import io

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..events import (
    broadcast_audience_membership_updated,
    broadcast_customer_created,
)
from ..models import Audience, AudienceMember, Customer


MAX_CSV_BYTES = 10 * 1024 * 1024


def _error(code, message, status=400, details=None):
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


def _find_customer(number, whatsapp_id):
    by_number = None
    by_whatsapp = None

    if number:
        number_matches = list(
            Customer.objects.filter(phone=number)[:2]
        )
        if len(number_matches) > 1:
            raise ValueError(
                "Number matches multiple customers in the database."
            )
        by_number = number_matches[0] if number_matches else None

    if whatsapp_id:
        by_whatsapp = (
            Customer.objects.filter(
                whatsapp_id=whatsapp_id
            ).first()
        )

    if by_number and by_whatsapp and by_number.id != by_whatsapp.id:
        raise ValueError(
            "Number and Whatsappid belong to different customers."
        )

    return by_number or by_whatsapp


def _normalise_header(value):
    return "".join(
        character
        for character in str(value or "").strip().lower()
        if character.isalnum()
    )


def _normalise_value(value):
    return str(value or "").strip()


def _report_text(rows):
    lines = ["Name\tNumber\tWhatsappid\tRemark"]
    for row in rows:
        lines.append(
            "\t".join(
                [
                    row["name"],
                    row["number"],
                    row["whatsapp_id"],
                    row["remark"],
                ]
            )
        )
    return "\n".join(lines)


@csrf_exempt
@require_POST
def audience_members_bulk(request, audience_id):
    try:
        audience = Audience.objects.get(id=audience_id)
    except Audience.DoesNotExist:
        return _error(
            "AUDIENCE_NOT_FOUND",
            "Audience not found.",
            404,
        )

    try:
        import json

        payload = json.loads(request.body or "{}")
    except (TypeError, ValueError):
        return _error(
            "VALIDATION_ERROR",
            "Request body must contain valid JSON.",
            400,
        )

    customer_ids = payload.get("customer_ids")

    if not isinstance(customer_ids, list) or not customer_ids:
        return _error(
            "VALIDATION_ERROR",
            "customer_ids must be a non-empty array.",
            400,
        )

    try:
        customer_ids = list(
            dict.fromkeys(int(customer_id) for customer_id in customer_ids)
        )
    except (TypeError, ValueError):
        return _error(
            "VALIDATION_ERROR",
            "customer_ids must contain only numeric customer IDs.",
            400,
        )

    customers = list(
        Customer.objects.filter(
            id__in=customer_ids,
            is_active=True,
            marketing_opted_in=True,
        )
    )
    customers_by_id = {customer.id: customer for customer in customers}

    invalid_ids = [
        customer_id
        for customer_id in customer_ids
        if customer_id not in customers_by_id
    ]

    if invalid_ids:
        return _error(
            "INELIGIBLE_CUSTOMERS",
            "One or more selected customers are no longer eligible.",
            409,
            {"customer_ids": invalid_ids},
        )

    existing_ids = set(
        AudienceMember.objects.filter(
            audience=audience,
            customer_id__in=customer_ids,
        ).values_list("customer_id", flat=True)
    )

    to_add = [
        customer
        for customer in customers
        if customer.id not in existing_ids
    ]

    try:
        with transaction.atomic():
            AudienceMember.objects.bulk_create(
                [
                    AudienceMember(
                        audience=audience,
                        customer=customer,
                    )
                    for customer in to_add
                ],
                ignore_conflicts=True,
            )

            final_selected_count = AudienceMember.objects.filter(
                audience=audience,
                customer_id__in=customer_ids,
            ).count()

            added_count = max(
                0,
                final_selected_count - len(existing_ids),
            )

            transaction.on_commit(
                lambda: broadcast_audience_membership_updated(
                    audience,
                    "bulk_added",
                )
            )

        # Re-read after the commit so the response is authoritative.
        final_existing_count = AudienceMember.objects.filter(
            audience=audience,
            customer_id__in=customer_ids,
        ).count()

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "audience_id": audience.id,
                    "requested": len(customer_ids),
                    "added": max(0, added_count),
                    "already_members": len(existing_ids),
                    "member_count": audience.members.count(),
                    "total_matched": final_existing_count,
                },
                "message": "Audience members added successfully.",
                "meta": {},
            },
            status=200,
        )

    except IntegrityError:
        return _error(
            "BULK_ADD_FAILED",
            "Unable to add the selected customers.",
            409,
        )
    except Exception:
        return _error(
            "INTERNAL_ERROR",
            "Unable to add audience members.",
            500,
        )


@csrf_exempt
@require_POST
def audience_members_import_csv(request, audience_id):
    try:
        audience = Audience.objects.get(id=audience_id)
    except Audience.DoesNotExist:
        return _error(
            "AUDIENCE_NOT_FOUND",
            "Audience not found.",
            404,
        )

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return _error(
            "VALIDATION_ERROR",
            "A CSV file is required.",
            400,
            {"field": "file"},
        )

    if uploaded_file.size > MAX_CSV_BYTES:
        return _error(
            "FILE_TOO_LARGE",
            "CSV file cannot exceed 10 MB.",
            413,
        )

    try:
        raw = uploaded_file.read()
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _error(
            "INVALID_CSV",
            "CSV file must be UTF-8 encoded.",
            400,
        )

    try:
        reader = csv.DictReader(io.StringIO(text))
        raw_headers = reader.fieldnames or []
        headers = {
            _normalise_header(header): header
            for header in raw_headers
            if header is not None
        }

        required = {
            "name": "Name",
            "number": "Number",
            "whatsappid": "Whatsappid",
        }
        missing = [
            display
            for normalised, display in required.items()
            if normalised not in headers
        ]

        if missing:
            return _error(
                "INVALID_CSV",
                "CSV is missing required columns.",
                400,
                {
                    "required_columns": [
                        "Name",
                        "Number",
                        "Whatsappid",
                    ],
                    "missing_columns": missing,
                },
            )

        rows = list(reader)

    except csv.Error:
        return _error(
            "INVALID_CSV",
            "Unable to read the CSV file.",
            400,
        )

    imported = 0
    created_customers = 0
    existing_customers = 0
    skipped = 0
    errors = 0
    report_rows = []
    created_customer_ids = []

    for row_number, row in enumerate(rows, start=2):
        name = _normalise_value(row.get(headers["name"]))
        number = _normalise_value(row.get(headers["number"]))
        whatsapp_id = _normalise_value(row.get(headers["whatsappid"]))

        if not name:
            errors += 1
            report_rows.append(
                {
                    "name": name,
                    "number": number,
                    "whatsapp_id": whatsapp_id,
                    "remark": f"Row {row_number}: Name is required.",
                }
            )
            continue

        if not number and not whatsapp_id:
            errors += 1
            report_rows.append(
                {
                    "name": name,
                    "number": number,
                    "whatsapp_id": whatsapp_id,
                    "remark": (
                        f"Row {row_number}: Number or Whatsappid is required."
                    ),
                }
            )
            continue

        # A new Customer requires a phone number in the current data model.
        row_created = False
        row_existing = False
        customer = None

        try:
            with transaction.atomic():
                customer = _find_customer(
                    number,
                    whatsapp_id,
                )

                if customer is None:
                    if not number:
                        raise ValueError(
                            "Number is required when creating a new customer."
                        )

                    customer = Customer.objects.create(
                        name=name,
                        phone=number,
                        whatsapp_id=whatsapp_id or None,
                        opt_in=True,
                        marketing_opted_in=True,
                        marketing_opted_in_at=timezone.now(),
                        tags=[],
                        custom_fields={},
                    )
                    row_created = True

                else:
                    row_existing = True

                    if not customer.is_active:
                        raise ValueError(
                            "Existing customer is inactive."
                        )

                    if not customer.marketing_opted_in:
                        raise ValueError(
                            "Existing customer is not marketing opted in. "
                            "CSV import will not change existing consent."
                        )

                if AudienceMember.objects.filter(
                    audience=audience,
                    customer=customer,
                ).exists():
                    raise ValueError(
                        "Customer is already a member of this audience."
                    )

                AudienceMember.objects.create(
                    audience=audience,
                    customer=customer,
                )

                transaction.on_commit(
                    lambda customer=customer, created=row_created: (
                        broadcast_customer_created(customer)
                        if created
                        else None
                    )
                )

            imported += 1

            if row_created:
                created_customers += 1

            if row_existing:
                existing_customers += 1

        except (ValueError, IntegrityError) as exc:
            errors += 1

            report_rows.append(
                {
                    "name": name,
                    "number": number,
                    "whatsapp_id": whatsapp_id,
                    "remark": f"Row {row_number}: {exc}",
                }
            )
        except Exception as exc:
            errors += 1
            report_rows.append(
                {
                    "name": name,
                    "number": number,
                    "whatsapp_id": whatsapp_id,
                    "remark": f"Row {row_number}: {exc}",
                }
            )

    if imported:
        transaction.on_commit(
            lambda: broadcast_audience_membership_updated(
                audience,
                "bulk_imported",
            )
        )

    report = _report_text(report_rows) if report_rows else ""

    return JsonResponse(
        {
            "success": True,
            "data": {
                "audience_id": audience.id,
                "total_rows": len(rows),
                "imported": imported,
                "created_customers": created_customers,
                "existing_customers": existing_customers,
                "skipped": skipped,
                "errors": errors,
                "report": report,
            },
            "message": (
                "CSV import completed."
                if not errors
                else "CSV import completed with errors."
            ),
            "meta": {},
        },
        status=200,
    )
