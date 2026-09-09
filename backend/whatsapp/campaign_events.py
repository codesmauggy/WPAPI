from django.utils import timezone

from .events import broadcast_dashboard_event
from .models import Campaign, CampaignRecipient


def _recipient_payload(recipient: CampaignRecipient) -> dict:
    return {
        "id": recipient.id,
        "phone": recipient.phone,
        "customer": (
            {
                "id": recipient.customer.id,
                "name": recipient.customer.name,
                "phone": recipient.customer.phone,
            }
            if recipient.customer
            else None
        ),
        "status": recipient.status,
        "whatsapp_message_id": recipient.whatsapp_message_id,
        "queued_at": recipient.queued_at.isoformat() if recipient.queued_at else None,
        "sent_at": recipient.sent_at.isoformat() if recipient.sent_at else None,
        "delivered_at": recipient.delivered_at.isoformat() if recipient.delivered_at else None,
        "read_at": recipient.read_at.isoformat() if recipient.read_at else None,
        "failed_at": recipient.failed_at.isoformat() if recipient.failed_at else None,
        "error_message": recipient.error_message or "",
        "created_at": recipient.created_at.isoformat(),
        "updated_at": recipient.updated_at.isoformat(),
    }


def broadcast_campaign_update(campaign_id: int, recipient_id: int | None = None) -> None:
    """Broadcast the current campaign state and, when supplied, its recipient state."""
    campaign = Campaign.objects.get(id=campaign_id)
    recipients = CampaignRecipient.objects.filter(campaign_id=campaign_id)

    total = recipients.count()
    pending = recipients.filter(status="PENDING").count()
    queued = recipients.filter(status="QUEUED").count()
    sending = recipients.filter(status="SENDING").count()
    sent = recipients.filter(status__in=["SENT", "DELIVERED", "READ"]).count()
    delivered = recipients.filter(status__in=["DELIVERED", "READ"]).count()
    read = recipients.filter(status="READ").count()
    failed = recipients.filter(status="FAILED").count()
    cancelled = recipients.filter(status="CANCELLED").count()
    completed = min(total, sent + failed + cancelled)

    recipient = None
    if recipient_id is not None:
        recipient = (
            CampaignRecipient.objects
            .select_related("customer")
            .filter(id=recipient_id, campaign_id=campaign_id)
            .first()
        )

    broadcast_dashboard_event(
        {
            "type": "campaign.updated",
            "campaign_id": campaign.id,
            "campaign": {
                "id": campaign.id,
                "name": campaign.name,
                "status": campaign.status,
                "statistics": {
                    "total": total,
                    "pending": pending,
                    "queued": queued,
                    "sending": sending,
                    "sent": sent,
                    "delivered": delivered,
                    "read": read,
                    "failed": failed,
                    "cancelled": cancelled,
                    "completed": completed,
                },
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
                "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
                "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
                "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
            },
            "recipient": _recipient_payload(recipient) if recipient else None,
        }
    )
