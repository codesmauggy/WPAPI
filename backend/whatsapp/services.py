from django.conf import settings
import requests
from django.utils import timezone

from .models import (
    Conversation,
    Message,
    WhatsAppPhoneNumber,
    WhatsAppTemplate,
)


class WhatsAppAPIError(Exception):
    """Raised when the WhatsApp API returns an error."""


from .events import broadcast_dashboard_event

def send_text_message(
    recipient_phone: str,
    message: str,
) -> dict:
    """
    Send a text message through the WhatsApp Cloud API.
    """

    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    access_token = settings.WHATSAPP_ACCESS_TOKEN
    api_version = settings.WHATSAPP_API_VERSION

    if not phone_number_id:
        raise WhatsAppAPIError(
            "WHATSAPP_PHONE_NUMBER_ID is not configured."
        )

    if not access_token:
        raise WhatsAppAPIError(
            "WHATSAPP_ACCESS_TOKEN is not configured."
        )

    if not api_version:
        raise WhatsAppAPIError(
            "WHATSAPP_API_VERSION is not configured."
        )

    url = (
        f"https://graph.facebook.com/"
        f"{api_version}/"
        f"{phone_number_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message,
        },
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    try:
        response_data = response.json()
    except ValueError:
        response_data = {
            "raw_response": response.text,
        }

    if not response.ok:
        raise WhatsAppAPIError(
            f"WhatsApp API error "
            f"{response.status_code}: "
            f"{response_data}"
        )

    return response_data

def get_whatsapp_templates(
    limit=100,
):
    """
    Fetch message templates from Meta.
    """

    waba_id = (
        settings.WHATSAPP_BUSINESS_ACCOUNT_ID
    )

    access_token = (
        settings.WHATSAPP_ACCESS_TOKEN
    )

    api_version = (
        settings.WHATSAPP_API_VERSION
    )

    if not waba_id:
        raise WhatsAppAPIError(
            "WHATSAPP_BUSINESS_ACCOUNT_ID "
            "is not configured."
        )

    url = (
        f"https://graph.facebook.com/"
        f"{api_version}/"
        f"{waba_id}/message_templates"
    )

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
    }

    params = {
        "limit": limit,
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    try:
        data = response.json()
    except ValueError:
        data = {
            "raw_response": response.text,
        }

    if not response.ok:
        raise WhatsAppAPIError(
            f"WhatsApp template API error "
            f"{response.status_code}: "
            f"{data}"
        )

    return data


def sync_whatsapp_templates():
    """
    Synchronize Meta WhatsApp templates
    into the local database.
    """

    data = get_whatsapp_templates()

    templates = data.get(
        "data",
        [],
    )

    created_count = 0
    updated_count = 0

    for item in templates:

        name = item.get(
            "name",
            "",
        )

        language = item.get(
            "language",
            "",
        )

        if not name or not language:
            continue

        template, created = (
            WhatsAppTemplate.objects.update_or_create(
                name=name,
                language=language,
                defaults={
                    "category": (
                        item.get(
                            "category",
                            "UTILITY",
                        )
                        or "UTILITY"
                    ).upper(),

                    "status": (
                        item.get(
                            "status",
                            "UNKNOWN",
                        )
                        or "UNKNOWN"
                    ).upper(),

                    "meta_template_id": (
                        item.get(
                            "id",
                            "",
                        )
                        or ""
                    ),

                    "components": (
                        item.get(
                            "components",
                            [],
                        )
                        or []
                    ),

                    "quality_score": (
                        item.get(
                            "quality_score",
                            {},
                        )
                        or {}
                    ),

                    "rejected_reason": (
                        item.get(
                            "rejected_reason",
                            "",
                        )
                        or ""
                    ),

                    "raw_payload": item,
                },
            )
        )

        if created:
            created_count += 1
            event_type = "template.created"
        else:
            updated_count += 1
            event_type = "template.updated"

        broadcast_dashboard_event({
            "type": event_type,
            "template": {
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
            },
        })

    return {
        "total": len(templates),
        "created": created_count,
        "updated": updated_count,
    }

def send_template_message(
    recipient_phone: str,
    template_name: str,
    language_code: str,
    components=None,
):
    """
    Send an approved WhatsApp template.
    """

    phone_number_id = (
        settings.WHATSAPP_PHONE_NUMBER_ID
    )

    access_token = (
        settings.WHATSAPP_ACCESS_TOKEN
    )

    api_version = (
        settings.WHATSAPP_API_VERSION
    )

    if not phone_number_id:
        raise WhatsAppAPIError(
            "WHATSAPP_PHONE_NUMBER_ID "
            "is not configured."
        )

    if not access_token:
        raise WhatsAppAPIError(
            "WHATSAPP_ACCESS_TOKEN "
            "is not configured."
        )

    url = (
        f"https://graph.facebook.com/"
        f"{api_version}/"
        f"{phone_number_id}/messages"
    )

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Content-Type": "application/json",
    }

    template = {
        "name": template_name,
        "language": {
            "code": language_code,
        },
    }

    if components:
        template["components"] = components

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "template",
        "template": template,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    try:
        data = response.json()
    except ValueError:
        data = {
            "raw_response": response.text,
        }

    if not response.ok:
        raise WhatsAppAPIError(
            f"WhatsApp template send error "
            f"{response.status_code}: "
            f"{data}"
        )

    return data

def send_template_to_customer(
    customer,
    template,
    components=None,
):
    """
    Send an approved WhatsApp template to a customer
    and create the outbound Message record.
    """

    result = send_template_message(
        recipient_phone=customer.phone,
        template_name=template.name,
        language_code=template.language,
        components=components,
    )

    whatsapp_message_id = None

    messages = result.get(
        "messages",
        [],
    )

    if messages:
        whatsapp_message_id = messages[0].get(
            "id"
        )

    conversation = (
        Conversation.objects
        .filter(
            customer=customer,
            phone_number__phone_number_id=(
                settings.WHATSAPP_PHONE_NUMBER_ID
            ),
            status="open",
        )
        .order_by("-created_at")
        .first()
    )

    if not conversation:
        phone_number = (
            WhatsAppPhoneNumber.objects
            .filter(
                phone_number_id=(
                    settings.WHATSAPP_PHONE_NUMBER_ID
                )
            )
            .first()
        )

        if not phone_number:
            raise WhatsAppAPIError(
                "Configured WhatsApp phone number "
                "was not found in the database."
            )

        conversation = Conversation.objects.create(
            customer=customer,
            phone_number=phone_number,
            status="open",
        )

    message = Message.objects.create(
        conversation=conversation,
        whatsapp_message_id=(
            whatsapp_message_id
        ),
        direction="outbound",
        message_type="template",
        text=(
            f"Template: {template.name}"
        ),
        status="sent",
        raw_payload=result,
    )

    conversation.last_message_at = timezone.now()

    conversation.save(
        update_fields=[
            "last_message_at",
            "updated_at",
        ]
    )

    return message