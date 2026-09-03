import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "GET":
        return verify_webhook(request)

    if request.method == "POST":
        return receive_webhook(request)

    return JsonResponse(
        {"error": "Method not allowed"},
        status=405,
    )


def verify_webhook(request):
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if (
        mode == "subscribe"
        and token == getattr(settings, "WHATSAPP_VERIFY_TOKEN", "")
    ):
        return HttpResponse(challenge)

    return HttpResponse("Verification failed", status=403)


def receive_webhook(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400,
        )

    print("WhatsApp webhook received:")
    print(
        json.dumps(
            payload,
            indent=2,
        )
    )

    try:
        from .webhooks import (
            process_whatsapp_webhook
        )

        process_whatsapp_webhook(payload)

    except Exception as exc:
        print(
            "Error processing WhatsApp webhook:"
        )
        print(exc)

        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "message": "Webhook processed",
        }
    )