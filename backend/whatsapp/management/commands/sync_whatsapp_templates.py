from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from whatsapp.services import (
    sync_whatsapp_templates,
    WhatsAppAPIError,
)


class Command(BaseCommand):

    help = (
        "Synchronize WhatsApp message "
        "templates from Meta."
    )

    def handle(self, *args, **options):

        self.stdout.write(
            "Synchronizing WhatsApp templates..."
        )

        try:
            result = (
                sync_whatsapp_templates()
            )

        except WhatsAppAPIError as exc:

            raise CommandError(
                str(exc)
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Template synchronization complete."
            )
        )

        self.stdout.write(
            f"Total:   {result['total']}"
        )

        self.stdout.write(
            f"Created: {result['created']}"
        )

        self.stdout.write(
            f"Updated: {result['updated']}"
        )