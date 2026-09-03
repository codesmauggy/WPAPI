from django.db import transaction

from .models import (
    AudienceMember,
    Campaign,
    CampaignRecipient,
)


class AudienceGenerationError(Exception):
    """Raised when campaign recipients cannot be generated."""


@transaction.atomic
def generate_campaign_recipients(
    campaign_id: int,
) -> dict:
    """
    Generate CampaignRecipient records from the campaign
    audience.

    IMPORTANT:
    This function ONLY creates PENDING recipient records.

    It does NOT:
    - send WhatsApp messages
    - call Meta
    - change customer consent
    """

    # --------------------------------------------------------
    # Load campaign
    # --------------------------------------------------------

    try:

        campaign = (
            Campaign.objects
            .select_related(
                "audience",
                "template",
                "phone_number",
            )
            .select_for_update()
            .get(
                id=campaign_id
            )
        )

    except Campaign.DoesNotExist:

        raise AudienceGenerationError(
            f"Campaign {campaign_id} does not exist."
        )

    # --------------------------------------------------------
    # Campaign status
    # --------------------------------------------------------

    if campaign.status not in (
        "DRAFT",
        "SCHEDULED",
        "PAUSED",
    ):

        raise AudienceGenerationError(
            f"Recipients cannot be generated "
            f"for campaign status: "
            f"{campaign.status}"
        )

    # --------------------------------------------------------
    # Audience
    # --------------------------------------------------------

    if not campaign.audience:

        raise AudienceGenerationError(
            "Campaign does not have an audience."
        )

    audience = campaign.audience

    if not audience.is_active:

        raise AudienceGenerationError(
            "Selected audience is inactive."
        )

    # --------------------------------------------------------
    # Audience members
    # --------------------------------------------------------

    members = (
        AudienceMember.objects
        .select_related(
            "customer"
        )
        .filter(
            audience=audience
        )
        .order_by("id")
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {

        "campaign_id": campaign.id,

        "campaign_name": campaign.name,

        "audience_id": audience.id,

        "audience_name": audience.name,

        "audience_members": 0,

        "eligible": 0,

        "created": 0,

        "existing": 0,

        "skipped_opted_out": 0,

        "skipped_inactive": 0,

        "skipped_no_phone": 0,

    }

    # --------------------------------------------------------
    # Process members
    # --------------------------------------------------------

    for member in members:

        result["audience_members"] += 1

        customer = member.customer

        # ----------------------------------------------------
        # Active customer
        # ----------------------------------------------------

        if not customer.is_active:

            result["skipped_inactive"] += 1

            continue

        # ----------------------------------------------------
        # Marketing consent
        # ----------------------------------------------------

        if not customer.marketing_opted_in:

            result["skipped_opted_out"] += 1

            continue

        # ----------------------------------------------------
        # Phone
        # ----------------------------------------------------

        if not customer.phone:

            result["skipped_no_phone"] += 1

            continue

        # ----------------------------------------------------
        # Existing recipient
        # ----------------------------------------------------

        existing = (
            CampaignRecipient.objects
            .filter(
                campaign=campaign,
                customer=customer,
            )
            .first()
        )

        if existing:

            result["existing"] += 1

            continue

        # ----------------------------------------------------
        # Eligible
        # ----------------------------------------------------

        result["eligible"] += 1

        # ----------------------------------------------------
        # Create recipient
        # ----------------------------------------------------

        CampaignRecipient.objects.create(

            campaign=campaign,

            customer=customer,

            phone=customer.phone,

            variables={},

            status="PENDING",
        )

        result["created"] += 1

    # --------------------------------------------------------
    # Update campaign total
    # --------------------------------------------------------

    campaign.total_recipients = (
        CampaignRecipient.objects
        .filter(
            campaign=campaign,
        )
        .exclude(
            status="CANCELLED",
        )
        .count()
    )

    campaign.save(
        update_fields=[
            "total_recipients",
            "updated_at",
        ]
    )

    return result