from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (
    require_GET,
    require_POST,
)

from .models import (
    Campaign,
    CampaignRecipient,
    WhatsAppPhoneNumber,
    Audience,
    WhatsAppTemplate,
)

from .campaigns import update_campaign_statistics

from .audiences import (
    AudienceGenerationError,
    generate_campaign_recipients,
)

from .campaign_preview import (
    CampaignPreviewError,
    preview_campaign,
)

from .tasks import queue_campaign
from .rate_limiter import reset_rate_limiter

# ============================================================
# Campaign Creation Options
# ============================================================

@require_GET
def campaign_options(request):
    """
    Return available options for creating a campaign.

    READ ONLY.
    """

    try:
        phone_numbers = (
            WhatsAppPhoneNumber.objects
            .filter(is_active=True)
            .select_related("business_account")
        )

        audiences = (
            Audience.objects
            .filter(is_active=True)
        )

        templates = (
            WhatsAppTemplate.objects
            .filter(status="APPROVED")
        )

        data = {
            "phone_numbers": [
                {
                    "id": phone.id,
                    "display_name": phone.display_name,
                    "phone_number": phone.phone_number,
                    "phone_number_id": phone.phone_number_id,
                }
                for phone in phone_numbers
            ],
            "audiences": [
                {
                    "id": audience.id,
                    "name": audience.name,
                    "description": audience.description,
                }
                for audience in audiences
            ],
            "templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "language": template.language,
                    "category": template.category,
                    "status": template.status,
                }
                for template in templates
            ],
        }

        return JsonResponse(
            {
                "success": True,
                "data": data,
            },
            status=200,
        )

    except Exception as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )


# ============================================================
# Create Campaign
# ============================================================

@csrf_exempt
@require_POST
def create_campaign(request):
    """
    Create a new campaign in DRAFT status.

    Does NOT generate recipients.
    Does NOT queue the campaign.
    Does NOT send WhatsApp messages.
    """

    import json

    try:
        body = json.loads(
            request.body.decode("utf-8")
        )

        name = str(
            body.get("name", "")
        ).strip()

        phone_number_id = body.get(
            "phone_number_id"
        )

        audience_id = body.get(
            "audience_id"
        )

        template_id = body.get(
            "template_id"
        )

        if not name:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Campaign name is required.",
                },
                status=400,
            )

        if not phone_number_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "WhatsApp phone number is required.",
                },
                status=400,
            )

        if not audience_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Audience is required.",
                },
                status=400,
            )

        if not template_id:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Template is required.",
                },
                status=400,
            )

        try:
            phone_number = (
                WhatsAppPhoneNumber.objects
                .get(
                    id=phone_number_id,
                    is_active=True,
                )
            )
        except WhatsAppPhoneNumber.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Selected WhatsApp phone number is not active or does not exist.",
                },
                status=400,
            )

        try:
            audience = (
                Audience.objects
                .get(
                    id=audience_id,
                    is_active=True,
                )
            )
        except Audience.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Selected audience is not active or does not exist.",
                },
                status=400,
            )

        try:
            template = (
                WhatsAppTemplate.objects
                .get(
                    id=template_id,
                    status="APPROVED",
                )
            )
        except WhatsAppTemplate.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Selected template is not approved or does not exist.",
                },
                status=400,
            )

        campaign = Campaign.objects.create(
            name=name,
            phone_number=phone_number,
            audience=audience,
            template=template,
            status="DRAFT",
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Campaign created successfully.",
                "data": {
                    "campaign_id": campaign.id,
                    "name": campaign.name,
                    "status": campaign.status,
                },
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid JSON request.",
            },
            status=400,
        )

    except Exception as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )


# ============================================================
# Campaign Preview
# ============================================================

@require_GET
def campaign_preview(
    request,
    campaign_id,
):
    """
    Preview campaign eligibility.

    Does NOT create recipients or send messages.
    """

    try:

        result = preview_campaign(
            campaign_id
        )

        return JsonResponse(
            {
                "success": True,
                "data": result,
            },
            status=200,
        )

    except CampaignPreviewError as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=400,
        )

    except Exception as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )


# ============================================================
# Generate Campaign Recipients
# ============================================================

@csrf_exempt
@require_POST
def generate_recipients(
    request,
    campaign_id,
):
    """
    Generate PENDING CampaignRecipient records.

    Does NOT send WhatsApp messages.
    """

    try:

        result = (
            generate_campaign_recipients(
                campaign_id
            )
        )

        return JsonResponse(
            {
                "success": True,

                "message": (
                    "Campaign recipients "
                    "generated successfully."
                ),

                "data": result,
            },

            status=200,
        )

    except AudienceGenerationError as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=400,
        )

    except Exception as exc:

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )


# ============================================================
# Queue Campaign
# ============================================================

@csrf_exempt
@require_POST
def queue_campaign_api(
    request,
    campaign_id,
):
    """
    Queue a campaign for asynchronous processing.
    """

    with transaction.atomic():

        try:

            campaign = (
                Campaign.objects
                .select_for_update()
                .select_related(
                    "template",
                    "audience",
                    "phone_number",
                )
                .get(
                    id=campaign_id
                )
            )

        except Campaign.DoesNotExist:

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        f"Campaign {campaign_id} "
                        "does not exist."
                    ),
                },
                status=404,
            )

        # ----------------------------------------------------
        # Validate status
        # ----------------------------------------------------

        if campaign.status not in (
            "DRAFT",
            "SCHEDULED",
            "PAUSED",
        ):

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Campaign cannot be queued "
                        f"from status: "
                        f"{campaign.status}"
                    ),
                },
                status=400,
            )

        # ----------------------------------------------------
        # Template
        # ----------------------------------------------------

        if not campaign.template:

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Campaign has no template."
                    ),
                },
                status=400,
            )

        if campaign.template.status != "APPROVED":

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Campaign template is "
                        "not approved."
                    ),
                },
                status=400,
            )

        # ----------------------------------------------------
        # Audience
        # ----------------------------------------------------

        if not campaign.audience:

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Campaign has no audience."
                    ),
                },
                status=400,
            )

        if not campaign.audience.is_active:

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Campaign audience "
                        "is inactive."
                    ),
                },
                status=400,
            )

        # ----------------------------------------------------
        # Pending recipients
        # ----------------------------------------------------

        pending_count = (
            CampaignRecipient.objects
            .filter(
                campaign=campaign,
                status="PENDING",
            )
            .count()
        )

        if pending_count == 0:

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Campaign has no "
                        "PENDING recipients."
                    ),
                },
                status=400,
            )

        # ----------------------------------------------------
        # RUNNING
        # ----------------------------------------------------

        reset_rate_limiter()
        campaign.status = "RUNNING"

        if not campaign.started_at:

            campaign.started_at = (
                timezone.now()
            )

        campaign.save(
            update_fields=[
                "status",
                "started_at",
                "updated_at",
            ]
        )

        # ----------------------------------------------------
        # Queue after DB commit
        # ----------------------------------------------------

        transaction.on_commit(
            lambda: queue_campaign.delay(
                campaign.id
            )
        )

    return JsonResponse(
        {
            "success": True,

            "message": (
                "Campaign queued successfully."
            ),

            "data": {
                "campaign_id": campaign.id,
                "status": "RUNNING",
                "queued_recipients": pending_count,
            },
        },

        status=202,
    )


# ============================================================
# Campaign Status
# ============================================================

@require_GET
def campaign_status(
    request,
    campaign_id,
):
    """
    Return live campaign progress.
    """

    try:

        campaign = (
            Campaign.objects
            .get(
                id=campaign_id
            )
        )

    except Campaign.DoesNotExist:

        return JsonResponse(
            {
                "success": False,
                "error": (
                    f"Campaign {campaign_id} "
                    "does not exist."
                ),
            },
            status=404,
        )

    recipients = (
        CampaignRecipient.objects
        .filter(
            campaign_id=campaign_id
        )
    )

    total = recipients.count()

    pending = recipients.filter(
        status="PENDING"
    ).count()

    sending = recipients.filter(
        status="SENDING"
    ).count()

    # --------------------------------------------------------
    # Successful delivery states
    # --------------------------------------------------------
    #
    # SENT already means the WhatsApp message was accepted.
    # DELIVERED means it was delivered.
    # READ means it was delivered and then read.
    #
    # Therefore:
    # sent = SENT + DELIVERED + READ
    # delivered = DELIVERED + READ
    #
    # These are aggregate counters, not mutually exclusive
    # workflow states.
    # --------------------------------------------------------

    sent = recipients.filter(
        status__in=[
            "SENT",
            "DELIVERED",
            "READ",
        ]
    ).count()

    delivered = recipients.filter(
        status__in=[
            "DELIVERED",
            "READ",
        ]
    ).count()

    read = recipients.filter(
        status="READ"
    ).count()

    failed = recipients.filter(
        status="FAILED"
    ).count()

    cancelled = recipients.filter(
        status="CANCELLED"
    ).count()

    # --------------------------------------------------------
    # Processed recipients
    # --------------------------------------------------------
    #
    # A recipient is processed once it has reached:
    #
    # SENT / DELIVERED / READ / FAILED / CANCELLED
    #
    # Since `sent` already includes SENT + DELIVERED + READ,
    # do not add delivered/read again.
    # --------------------------------------------------------

    processed = min(
        total,
        sent
        + failed
        + cancelled,
    )

    # --------------------------------------------------------
    # Delivery progress
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Progress is based ONLY on delivered recipients.
    #
    # Failed recipients do not increase delivery progress.
    #
    # Example:
    # 100 total
    # 75 delivered
    # 25 failed
    # => 75%
    # --------------------------------------------------------

    if total > 0:
        progress = round(
            (
                delivered
                / total
            ) * 100,
            2,
        )
    else:
        progress = 0.0

    # --------------------------------------------------------
    # Automatically complete campaign
    # --------------------------------------------------------

    if (
        total > 0
        and processed >= total
        and campaign.status == "RUNNING"
    ):
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

    return JsonResponse(
        {
            "success": True,
            "data": {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "status": campaign.status,
                "statistics": {
                    "total": total,
                    "pending": pending,
                    "sending": sending,
                    "sent": sent,
                    "delivered": delivered,
                    "read": read,
                    "failed": failed,
                    "cancelled": cancelled,
                    "completed": processed,
                },
                "progress": progress,
            },
        },
        status=200,
    )


# ============================================================
# Campaign Recipients
# ============================================================

@require_GET
def campaign_recipients(request, campaign_id):
    """
    Return recipient-level delivery information for a campaign.

    READ ONLY.
    This endpoint does not modify campaigns, recipients,
    queues, or WhatsApp messages.
    """

    try:
        campaign = (
            Campaign.objects
            .select_related(
                "template",
                "audience",
                "phone_number",
            )
            .get(id=campaign_id)
        )

    except Campaign.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    f"Campaign {campaign_id} "
                    "does not exist."
                ),
            },
            status=404,
        )

    recipients = (
        CampaignRecipient.objects
        .filter(campaign_id=campaign_id)
        .select_related("customer")
        .order_by("-created_at")
    )

    data = []

    for recipient in recipients:
        data.append(
            {
                "id": recipient.id,

                "phone": recipient.phone,

                "customer": {
                    "id": recipient.customer.id,
                    "name": recipient.customer.name,
                    "phone": recipient.customer.phone,
                } if recipient.customer else None,

                "status": recipient.status,

                "whatsapp_message_id": (
                    recipient.whatsapp_message_id
                ),

                "queued_at": (
                    recipient.queued_at.isoformat()
                    if recipient.queued_at
                    else None
                ),

                "sent_at": (
                    recipient.sent_at.isoformat()
                    if recipient.sent_at
                    else None
                ),

                "delivered_at": (
                    recipient.delivered_at.isoformat()
                    if recipient.delivered_at
                    else None
                ),

                "read_at": (
                    recipient.read_at.isoformat()
                    if recipient.read_at
                    else None
                ),

                "failed_at": (
                    recipient.failed_at.isoformat()
                    if recipient.failed_at
                    else None
                ),

                "error_message": (
                    recipient.error_message
                    or ""
                ),

                "created_at": (
                    recipient.created_at.isoformat()
                ),

                "updated_at": (
                    recipient.updated_at.isoformat()
                ),
            }
        )

    return JsonResponse(
        {
            "success": True,
            "data": {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "total": len(data),
                "recipients": data,
            },
        },
        status=200,
    )


# ============================================================
# Pause Campaign
# ============================================================

@csrf_exempt
@require_POST
def pause_campaign(
    request,
    campaign_id,
):
    """
    Pause a running campaign.

    Existing SENT/DELIVERED/READ recipients are untouched.

    PENDING recipients remain PENDING.
    """

    with transaction.atomic():

        try:

            campaign = (
                Campaign.objects
                .select_for_update()
                .get(
                    id=campaign_id
                )
            )

        except Campaign.DoesNotExist:

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        f"Campaign {campaign_id} "
                        "does not exist."
                    ),
                },
                status=404,
            )

        # ----------------------------------------------------
        # Only RUNNING campaigns can be paused
        # ----------------------------------------------------

        if campaign.status != "RUNNING":

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Only RUNNING campaigns "
                        "can be paused. "
                        f"Current status: "
                        f"{campaign.status}"
                    ),
                },
                status=400,
            )

        reset_rate_limiter()
        campaign.status = "PAUSED"

        campaign.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return JsonResponse(
        {
            "success": True,

            "message": (
                "Campaign paused successfully."
            ),

            "data": {
                "campaign_id": campaign.id,
                "status": campaign.status,
            },
        },

        status=200,
    )


# ============================================================
# Resume Campaign
# ============================================================

@csrf_exempt
@require_POST
def resume_campaign(
    request,
    campaign_id,
):
    """
    Resume a paused campaign.

    Only remaining PENDING recipients are queued.
    """

    with transaction.atomic():

        try:

            campaign = (
                Campaign.objects
                .select_for_update()
                .get(
                    id=campaign_id
                )
            )

        except Campaign.DoesNotExist:

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        f"Campaign {campaign_id} "
                        "does not exist."
                    ),
                },
                status=404,
            )

        # ----------------------------------------------------
        # Only PAUSED campaigns can resume
        # ----------------------------------------------------

        if campaign.status != "PAUSED":

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Only PAUSED campaigns "
                        "can be resumed. "
                        f"Current status: "
                        f"{campaign.status}"
                    ),
                },
                status=400,
            )

        # ----------------------------------------------------
        # Find remaining PENDING recipients
        # ----------------------------------------------------

        pending_count = (
            CampaignRecipient.objects
            .filter(
                campaign=campaign,
                status="PENDING",
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

            return JsonResponse(
                {
                    "success": True,

                    "message": (
                        "Campaign has no remaining "
                        "pending recipients."
                    ),

                    "data": {
                        "campaign_id": campaign.id,
                        "status": "COMPLETED",
                        "queued_recipients": 0,
                    },
                },

                status=200,
            )

        # ----------------------------------------------------
        # RUNNING
        # ----------------------------------------------------

        reset_rate_limiter()
        campaign.status = "RUNNING"

        campaign.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # ----------------------------------------------------
        # Queue remaining recipients
        # ----------------------------------------------------

        transaction.on_commit(
            lambda: queue_campaign.delay(
                campaign.id
            )
        )

    return JsonResponse(
        {
            "success": True,

            "message": (
                "Campaign resumed successfully."
            ),

            "data": {
                "campaign_id": campaign.id,
                "status": "RUNNING",
                "queued_recipients": pending_count,
            },
        },

        status=202,
    )


# ============================================================
# Cancel Campaign
# ============================================================

@csrf_exempt
@require_POST
def cancel_campaign(
    request,
    campaign_id,
):
    """
    Cancel a campaign.

    Only PENDING recipients are cancelled.

    SENT, DELIVERED and READ recipients remain unchanged.
    """

    with transaction.atomic():

        try:

            campaign = (
                Campaign.objects
                .select_for_update()
                .get(
                    id=campaign_id
                )
            )

        except Campaign.DoesNotExist:

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        f"Campaign {campaign_id} "
                        "does not exist."
                    ),
                },
                status=404,
            )

        # ----------------------------------------------------
        # Allowed states
        # ----------------------------------------------------

        if campaign.status not in (
            "RUNNING",
            "PAUSED",
            "SCHEDULED",
        ):

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Campaign cannot be cancelled "
                        f"from status: "
                        f"{campaign.status}"
                    ),
                },
                status=400,
            )

        # ----------------------------------------------------
        # Cancel pending recipients
        # ----------------------------------------------------

        cancelled_count = (
            CampaignRecipient.objects
            .filter(
                campaign=campaign,
                status="PENDING",
            )
            .update(
                status="CANCELLED",
                error_message=(
                    "Campaign cancelled."
                ),
                updated_at=timezone.now(),
            )
        )

        # ----------------------------------------------------
        # Cancel campaign
        # ----------------------------------------------------

        campaign.status = "CANCELLED"

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

        # Keep persisted campaign counters synchronized after
        # pending recipients are moved to CANCELLED.
        update_campaign_statistics(campaign)

    return JsonResponse(
        {
            "success": True,

            "message": (
                "Campaign cancelled successfully."
            ),

            "data": {
                "campaign_id": campaign.id,
                "status": "CANCELLED",
                "cancelled_recipients": (
                    cancelled_count
                ),
            },
        },

        status=200,
    )

# ============================================================
# Campaign List
# ============================================================

@require_GET
def campaign_list(request):
    """
    Return campaigns for the frontend.

    READ ONLY.
    This endpoint does not modify campaigns,
    recipients, queues, or WhatsApp messages.
    """

    try:
        campaigns = (
            Campaign.objects
            .select_related(
                "template",
                "audience",
                "phone_number",
            )
            .annotate(
                live_total=Count(
                    "recipients",
                    distinct=True,
                ),
                live_sent=Count(
                    "recipients",
                    filter=Q(
                        recipients__status__in=[
                            "SENT",
                            "DELIVERED",
                            "READ",
                        ]
                    ),
                    distinct=True,
                ),
                live_delivered=Count(
                    "recipients",
                    filter=Q(
                        recipients__status__in=[
                            "DELIVERED",
                            "READ",
                        ]
                    ),
                    distinct=True,
                ),
                live_read=Count(
                    "recipients",
                    filter=Q(
                        recipients__status="READ"
                    ),
                    distinct=True,
                ),
                live_failed=Count(
                    "recipients",
                    filter=Q(
                        recipients__status="FAILED"
                    ),
                    distinct=True,
                ),
                live_pending=Count(
                    "recipients",
                    filter=Q(
                        recipients__status="PENDING"
                    ),
                    distinct=True,
                ),
                live_sending=Count(
                    "recipients",
                    filter=Q(
                        recipients__status="SENDING"
                    ),
                    distinct=True,
                ),
                live_cancelled=Count(
                    "recipients",
                    filter=Q(
                        recipients__status="CANCELLED"
                    ),
                    distinct=True,
                ),
            )
            .order_by("-created_at")
        )

        data = []

        for campaign in campaigns:
            data.append(
                {
                    "id": campaign.id,
                    "name": campaign.name,
                    "status": campaign.status,

                    "audience": (
                        {
                            "id": campaign.audience.id,
                            "name": campaign.audience.name,
                        }
                        if campaign.audience
                        else None
                    ),

                    "template": (
                        {
                            "name": campaign.template.name,
                            "language": campaign.template.language,
                            "status": campaign.template.status,
                        }
                        if campaign.template
                        else None
                    ),

                    "phone_number": (
                        {
                            "id": campaign.phone_number.id,
                            "display_name": (
                                campaign.phone_number.display_name
                            ),
                            "phone_number": (
                                campaign.phone_number.phone_number
                            ),
                        }
                        if campaign.phone_number
                        else None
                    ),

                    "statistics": {
                        # Read live recipient state instead of relying
                        # on cached Campaign counter fields. This keeps
                        # the campaign list accurate after a direct
                        # Celery/API failure, including HTTP 401 errors.
                        "total": campaign.live_total,
                        "pending": campaign.live_pending,
                        "sending": campaign.live_sending,
                        "sent": campaign.live_sent,
                        "delivered": campaign.live_delivered,
                        "read": campaign.live_read,
                        "failed": campaign.live_failed,
                        "cancelled": campaign.live_cancelled,
                        "completed": (
                            campaign.live_sent
                            + campaign.live_delivered
                            + campaign.live_read
                            + campaign.live_failed
                            + campaign.live_cancelled
                        ),
                    },

                    "scheduled_at": (
                        campaign.scheduled_at.isoformat()
                        if campaign.scheduled_at
                        else None
                    ),

                    "started_at": (
                        campaign.started_at.isoformat()
                        if campaign.started_at
                        else None
                    ),

                    "completed_at": (
                        campaign.completed_at.isoformat()
                        if campaign.completed_at
                        else None
                    ),

                    "created_at": (
                        campaign.created_at.isoformat()
                        if campaign.created_at
                        else None
                    ),

                    "updated_at": (
                        campaign.updated_at.isoformat()
                        if campaign.updated_at
                        else None
                    ),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "data": data,
            },
            status=200,
        )

    except Exception as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )