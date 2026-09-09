from django.db import transaction
from django.utils import timezone

from .models import Campaign, CampaignRecipient
from .campaign_events import broadcast_campaign_update


def get_next_recipient():
    """
    Atomically claim the next available recipient.

    Flow:

        PENDING → QUEUED

    Only RUNNING campaigns are considered.

    The recipient is claimed before the Celery send task
    is created, preventing the dispatcher from selecting
    the same recipient repeatedly.
    """

    with transaction.atomic():

        recipient = (
            CampaignRecipient.objects
            .select_for_update(skip_locked=True)
            .select_related(
                "campaign",
                "customer",
            )
            .filter(
                status="PENDING",
                campaign__status="RUNNING",
            )
            .order_by("id")
            .first()
        )

        if recipient is None:
            return None

        # Atomically claim the recipient.
        recipient.status = "QUEUED"
        recipient.queued_at = timezone.now()

        recipient.save(
            update_fields=[
                "status",
                "queued_at",
                "updated_at",
            ]
        )

        transaction.on_commit(
            lambda: broadcast_campaign_update(
                campaign_id=recipient.campaign_id,
                recipient_id=recipient.id,
            )
        )

        return recipient


def has_pending_recipients():
    """
    Return True when at least one RUNNING campaign has a
    PENDING recipient.
    """

    return CampaignRecipient.objects.filter(
        status="PENDING",
        campaign__status="RUNNING",
    ).exists()