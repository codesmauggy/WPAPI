from django.contrib import admin

from .models import (
    WhatsAppBusinessAccount,
    WhatsAppPhoneNumber,
    Customer,
    Conversation,
    Message,
    WhatsAppTemplate,
    Audience,
    AudienceMember,
    Campaign,
    CampaignRecipient,
    WhatsAppSystemSettings,
)

# ============================================================
# WhatsApp Business Account
# ============================================================

@admin.register(WhatsAppBusinessAccount)
class WhatsAppBusinessAccountAdmin(
    admin.ModelAdmin
):

    list_display = (
        "name",
        "business_account_id",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "business_account_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# ============================================================
# WhatsApp Phone Number
# ============================================================

@admin.register(WhatsAppPhoneNumber)
class WhatsAppPhoneNumberAdmin(
    admin.ModelAdmin
):

    list_display = (
        "display_name",
        "phone_number",
        "phone_number_id",
        "business_account",
        "is_active",
    )

    list_filter = (
        "is_active",
        "business_account",
    )

    search_fields = (
        "display_name",
        "phone_number",
        "phone_number_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# ============================================================
# Customer
# ============================================================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "phone",
        "whatsapp_id",
        "status",
        "marketing_opted_in",
        "is_active",
        "last_message_at",
        "created_at",
    )

    list_filter = (
        "status",
        "marketing_opted_in",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "whatsapp_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_message_at",
    )

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "phone",
                    "whatsapp_id",
                    "status",
                    "is_active",
                )
            },
        ),
        (
            "Marketing Consent",
            {
                "fields": (
                    "opt_in",
                    "marketing_opted_in",
                    "marketing_opted_in_at",
                    "marketing_opted_out_at",
                )
            },
        ),
        (
            "Segmentation",
            {
                "fields": (
                    "tags",
                    "custom_fields",
                )
            },
        ),
        (
            "Activity",
            {
                "fields": (
                    "last_message_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# ============================================================
# Conversation
# ============================================================

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):

    list_display = (
        "customer",
        "phone_number",
        "status",
        "last_message_at",
        "created_at",
    )

    list_filter = (
        "status",
        "phone_number",
    )

    search_fields = (
        "customer__name",
        "customer__phone",
        "customer__whatsapp_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# ============================================================
# Message
# ============================================================

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "conversation",
        "direction",
        "message_type",
        "status",
        "whatsapp_message_id",
        "created_at",
    )

    list_filter = (
        "direction",
        "message_type",
        "status",
        "created_at",
    )

    search_fields = (
        "whatsapp_message_id",
        "text",
        "conversation__customer__name",
        "conversation__customer__phone",
    )

    readonly_fields = (
        "created_at",
    )


# ============================================================
# WhatsApp Template
# ============================================================

@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(
    admin.ModelAdmin
):

    list_display = (
        "name",
        "language",
        "category",
        "status",
        "meta_template_id",
        "synced_at",
    )

    list_filter = (
        "category",
        "status",
        "language",
    )

    search_fields = (
        "name",
        "meta_template_id",
    )

    readonly_fields = (
        "meta_template_id",
        "components",
        "quality_score",
        "raw_payload",
        "synced_at",
        "created_at",
        "updated_at",
    )


# ============================================================
# Audience
# ============================================================

@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "member_count",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = "Members"


# ============================================================
# Audience Member
# ============================================================

@admin.register(AudienceMember)
class AudienceMemberAdmin(admin.ModelAdmin):

    list_display = (
        "audience",
        "customer",
        "customer_phone",
        "created_at",
    )

    list_filter = (
        "audience",
        "created_at",
    )

    search_fields = (
        "customer__name",
        "customer__phone",
        "customer__whatsapp_id",
        "audience__name",
    )

    readonly_fields = (
        "created_at",
    )

    def customer_phone(self, obj):
        return obj.customer.phone

    customer_phone.short_description = "Phone"


# ============================================================
# Campaign
# ============================================================

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "audience",
        "template",
        "phone_number",
        "status",
        "total_recipients",
        "sent_count",
        "delivered_count",
        "read_count",
        "failed_count",
        "scheduled_at",
        "created_at",
    )

    list_filter = (
        "status",
        "template",
        "audience",
        "phone_number",
        "created_at",
    )

    search_fields = (
        "name",
        "audience__name",
        "template__name",
    )

    readonly_fields = (
        "total_recipients",
        "sent_count",
        "delivered_count",
        "read_count",
        "failed_count",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    )


# ============================================================
# Campaign Recipient
# ============================================================

@admin.register(CampaignRecipient)
class CampaignRecipientAdmin(
    admin.ModelAdmin
):

    list_display = (
        "campaign",
        "customer",
        "phone",
        "status",
        "whatsapp_message_id",
        "sent_at",
        "delivered_at",
        "read_at",
        "failed_at",
    )

    list_filter = (
        "status",
        "campaign",
        "created_at",
    )

    search_fields = (
        "phone",
        "customer__name",
        "customer__phone",
        "customer__whatsapp_id",
        "whatsapp_message_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

# ============================================================
# WhatsApp System Settings
# ============================================================

@admin.register(WhatsAppSystemSettings)
class WhatsAppSystemSettingsAdmin(admin.ModelAdmin):

    list_display = (
        "enabled",
        "interval_seconds",
        "updated_at",
    )

    readonly_fields = (
        "updated_at",
    )

    fieldsets = (
        (
            "Global WhatsApp Sending",
            {
                "fields": (
                    "enabled",
                    "interval_seconds",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "updated_at",
                ),
            },
        ),
    )

    def has_add_permission(
        self,
        request,
    ):
        """
        Allow only one settings record.
        """

        return not WhatsAppSystemSettings.objects.exists()

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        """
        Prevent deleting global settings.
        """

        return False