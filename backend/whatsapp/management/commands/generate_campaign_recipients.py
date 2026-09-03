from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from whatsapp.audiences import (
    AudienceGenerationError,
    generate_campaign_recipients,
)


class Command(BaseCommand):

    help = (
        "Generate campaign recipients from "
        "the campaign audience."
    )

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
            f"Generating recipients for "
            f"campaign {campaign_id}..."
        )

        try:

            result = (
                generate_campaign_recipients(
                    campaign_id
                )
            )

        except AudienceGenerationError as exc:

            raise CommandError(
                str(exc)
            )

        except Exception as exc:

            raise CommandError(
                f"Unexpected error: {exc}"
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Recipient generation complete."
            )
        )

        self.stdout.write(
            f"Audience members: "
            f"{result['audience_members']}"
        )

        self.stdout.write(
            f"Eligible: "
            f"{result['eligible']}"
        )

        self.stdout.write(
            f"Created: "
            f"{result['created']}"
        )

        self.stdout.write(
            f"Existing: "
            f"{result['existing']}"
        )

        self.stdout.write(
            f"Skipped - opted out: "
            f"{result['skipped_opt_out']}"
        )

        self.stdout.write(
            f"Skipped - inactive: "
            f"{result['skipped_inactive']}"
        )

        self.stdout.write(
            f"Skipped - no phone: "
            f"{result['skipped_no_phone']}"
        )

        self.stdout.write(
            f"Skipped - duplicate: "
            f"{result['skipped_duplicate']}"
        )