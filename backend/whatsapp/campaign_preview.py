from .models import (
    AudienceMember,
    Campaign,
    CampaignRecipient,
)


class CampaignPreviewError(Exception):
    """Raised when a campaign preview cannot be generated."""


def preview_campaign(
    campaign_id: int,
) -> dict:
    """
    Preview a campaign without:

    - creating CampaignRecipient records
    - changing recipient status
    - sending WhatsApp messages

    The function only calculates campaign eligibility.
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
            .get(
                id=campaign_id
            )
        )

    except Campaign.DoesNotExist:

        raise CampaignPreviewError(
            f"Campaign {campaign_id} does not exist."
        )

    # --------------------------------------------------------
    # Audience check
    # --------------------------------------------------------

    if not campaign.audience:

        raise CampaignPreviewError(
            "Campaign does not have an audience."
        )

    audience = campaign.audience

    # --------------------------------------------------------
    # Audience active check
    # --------------------------------------------------------

    if not audience.is_active:

        raise CampaignPreviewError(
            "Selected audience is inactive."
        )

    # --------------------------------------------------------
    # Template check
    # --------------------------------------------------------

    if not campaign.template:

        raise CampaignPreviewError(
            "Campaign does not have a template."
        )

    # --------------------------------------------------------
    # Get audience members
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
    # Preview result
    # --------------------------------------------------------

    result = {

        "campaign_id": campaign.id,

        "campaign_name": campaign.name,

        "audience_id": audience.id,

        "audience_name": audience.name,

        "template_name": campaign.template.name,

        "template_language": (
            campaign.template.language
        ),

        "audience_members": 0,

        "eligible": 0,

        "already_in_campaign": 0,

        "opted_out": 0,

        "inactive": 0,

        "no_phone": 0,

        "new_recipients": 0,
    }

    # --------------------------------------------------------
    # Evaluate every audience member
    # --------------------------------------------------------

    for member in members:

        result["audience_members"] += 1

        customer = member.customer

        # ----------------------------------------------------
        # Customer active
        # ----------------------------------------------------

        if not customer.is_active:

            result["inactive"] += 1

            continue

        # ----------------------------------------------------
        # Marketing consent
        # ----------------------------------------------------

        if not customer.marketing_opted_in:

            result["opted_out"] += 1

            continue

        # ----------------------------------------------------
        # Phone number
        # ----------------------------------------------------

        if not customer.phone:

            result["no_phone"] += 1

            continue

        # ----------------------------------------------------
        # Already exists in campaign
        # ----------------------------------------------------

        existing = (
            CampaignRecipient.objects
            .filter(
                campaign=campaign,
                customer=customer,
            )
            .exists()
        )

        if existing:

            result["already_in_campaign"] += 1

            continue

        # ----------------------------------------------------
        # Eligible
        # ----------------------------------------------------

        result["eligible"] += 1

        result["new_recipients"] += 1

    return result