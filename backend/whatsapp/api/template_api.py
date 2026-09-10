from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from whatsapp.models import WhatsAppTemplate
from whatsapp.services import WhatsAppAPIError, sync_whatsapp_templates
from whatsapp.events import broadcast_dashboard_event


def serialize_template(template):
    return {
        "id": template.id,
        "name": template.name,
        "language": template.language,
        "category": template.category,
        "status": template.status,
        "meta_template_id": template.meta_template_id,
        "components": template.components,
        "quality_score": template.quality_score,
        "rejected_reason": template.rejected_reason,
        "synced_at": template.synced_at.isoformat() if template.synced_at else None,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


@require_GET
def template_list(request):
    """List locally synchronized WhatsApp templates."""
    try:
        queryset = WhatsAppTemplate.objects.all()

        search = request.GET.get("search", "").strip()
        category = request.GET.get("category", "").strip().upper()
        status = request.GET.get("status", "").strip().upper()
        language = request.GET.get("language", "").strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(meta_template_id__icontains=search)
            )

        if category:
            queryset = queryset.filter(category=category)

        if status:
            queryset = queryset.filter(status=status)

        if language:
            queryset = queryset.filter(language=language)

        templates = list(queryset.order_by("-updated_at", "-id"))

        languages = list(
            WhatsAppTemplate.objects.values_list("language", flat=True)
            .distinct()
            .order_by("language")
        )

        return JsonResponse(
            {
                "success": True,
                "data": [serialize_template(template) for template in templates],
                "message": "Templates retrieved successfully.",
                "meta": {
                    "total": len(templates),
                    "languages": languages,
                },
            },
            status=200,
        )
    except Exception as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
                "message": "Unable to retrieve templates.",
            },
            status=500,
        )


@require_GET
def template_detail(request, template_id):
    """Retrieve one synchronized WhatsApp template."""
    try:
        template = WhatsAppTemplate.objects.get(id=template_id)
    except WhatsAppTemplate.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "error": "TEMPLATE_NOT_FOUND",
                "message": "Template not found.",
            },
            status=404,
        )

    return JsonResponse(
        {
            "success": True,
            "data": serialize_template(template),
            "message": "Template retrieved successfully.",
            "meta": {},
        },
        status=200,
    )


@csrf_exempt
@require_POST
def template_sync(request):
    """Synchronize WhatsApp templates from Meta."""
    try:
        result = sync_whatsapp_templates()

        broadcast_dashboard_event(
            {
                "type": "template.sync.completed",
                "result": result,
            }
        )

        return JsonResponse(
            {
                "success": True,
                "data": result,
                "message": "Templates synchronized successfully.",
                "meta": {},
            },
            status=200,
        )
    except WhatsAppAPIError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
                "message": "Template synchronization failed.",
            },
            status=502,
        )
    except Exception as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
                "message": "Template synchronization failed.",
            },
            status=500,
        )
