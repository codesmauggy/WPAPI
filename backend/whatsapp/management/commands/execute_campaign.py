from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from whatsapp.campaigns import (
    CampaignExecutionError,
    execute_campaign,
)


class Command(BaseCommand):

    help = "Execute a WhatsApp campaign."

    def add_arguments(self, parser):

        parser.add_argument(
            "campaign_id",
            type=int,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        campaign_id = options[
            "campaign_id"
        ]

        self.stdout.write(
            f"Executing campaign "
            f"{campaign_id}..."
        )

        try:

            result = execute_campaign(
                campaign_id
            )

        except CampaignExecutionError as exc:

            raise CommandError(
                str(exc)
            )

        except Exception as exc:

            raise CommandError(
                f"Unexpected error: {exc}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Campaign execution complete."
            )
        )

        self.stdout.write(
            f"Total:  {result['total']}"
        )

        self.stdout.write(
            f"Sent:   {result['sent']}"
        )

        self.stdout.write(
            f"Failed: {result['failed']}"
        )