from django.db import models


# ============================================================
# WhatsApp Business Account
# ============================================================

class WhatsAppBusinessAccount(models.Model):

    name = models.CharField(
        max_length=255,
    )

    business_account_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.name


# ============================================================
# WhatsApp Phone Number
# ============================================================

class WhatsAppPhoneNumber(models.Model):

    business_account = models.ForeignKey(
        WhatsAppBusinessAccount,
        on_delete=models.CASCADE,
        related_name="phone_numbers",
    )

    display_name = models.CharField(
        max_length=255,
    )

    phone_number = models.CharField(
        max_length=30,
    )

    phone_number_id = models.CharField(
        max_length=100,
        unique=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.display_name} "
            f"({self.phone_number})"
        )


# ============================================================
# Customer
# ============================================================

class Customer(models.Model):

    name = models.CharField(
        max_length=255,
        blank=True,
    )

    phone = models.CharField(
        max_length=30,
    )

    whatsapp_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    # Existing opt-in field
    # Kept for compatibility with existing code/data.
    opt_in = models.BooleanField(
        default=False,
    )

    # --------------------------------------------------------
    # Marketing Consent
    # --------------------------------------------------------

    marketing_opted_in = models.BooleanField(
        default=False,
    )

    marketing_opted_in_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    marketing_opted_out_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # --------------------------------------------------------
    # Customer Segmentation
    # --------------------------------------------------------

    tags = models.JSONField(
        default=list,
        blank=True,
    )

    custom_fields = models.JSONField(
        default=dict,
        blank=True,
    )

    # --------------------------------------------------------
    # Activity
    # --------------------------------------------------------

    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # --------------------------------------------------------
    # Customer Status
    # --------------------------------------------------------

    is_active = models.BooleanField(
        default=True,
    )

    status = models.CharField(
        max_length=30,
        default="ACTIVE",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=["phone"],
                name="customer_phone_idx",
            ),
            models.Index(
                fields=["marketing_opted_in"],
                name="customer_marketing_optin_idx",
            ),
            models.Index(
                fields=["is_active"],
                name="customer_active_idx",
            ),
            models.Index(
                fields=["status"],
                name="customer_status_idx",
            ),
        ]

    def __str__(self):
        return self.name or self.phone


# ============================================================
# Conversation
# ============================================================

class Conversation(models.Model):

    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    phone_number = models.ForeignKey(
        WhatsAppPhoneNumber,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.customer} - "
            f"{self.status}"
        )


# ============================================================
# Message
# ============================================================

class Message(models.Model):

    DIRECTION_CHOICES = [
        ("inbound", "Inbound"),
        ("outbound", "Outbound"),
    ]

    STATUS_CHOICES = [
        ("received", "Received"),
        ("queued", "Queued"),
        ("sending", "Sending"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
        ("failed", "Failed"),
    ]

    MESSAGE_TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("document", "Document"),
        ("interactive", "Interactive"),
        ("template", "Template"),
        ("unknown", "Unknown"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    whatsapp_message_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    direction = models.CharField(
        max_length=20,
        choices=DIRECTION_CHOICES,
    )

    message_type = models.CharField(
        max_length=30,
        choices=MESSAGE_TYPE_CHOICES,
        default="unknown",
    )

    text = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="received",
    )

    # Dashboard/operator read state. This is intentionally
    # separate from WhatsApp delivery status above.
    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    raw_payload = models.JSONField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.direction} - "
            f"{self.message_type}"
        )


# ============================================================
# WhatsApp Template
# ============================================================

class WhatsAppTemplate(models.Model):

    CATEGORY_CHOICES = [
        (
            "AUTHENTICATION",
            "Authentication",
        ),
        (
            "MARKETING",
            "Marketing",
        ),
        (
            "UTILITY",
            "Utility",
        ),
    ]

    STATUS_CHOICES = [
        (
            "APPROVED",
            "Approved",
        ),
        (
            "PENDING",
            "Pending",
        ),
        (
            "REJECTED",
            "Rejected",
        ),
        (
            "PAUSED",
            "Paused",
        ),
        (
            "DISABLED",
            "Disabled",
        ),
        (
            "UNKNOWN",
            "Unknown",
        ),
    ]

    name = models.CharField(
        max_length=255,
    )

    language = models.CharField(
        max_length=50,
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="UTILITY",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="UNKNOWN",
    )

    meta_template_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    components = models.JSONField(
        default=list,
        blank=True,
    )

    quality_score = models.JSONField(
        default=dict,
        blank=True,
    )

    rejected_reason = models.TextField(
        blank=True,
        default="",
    )

    raw_payload = models.JSONField(
        default=dict,
        blank=True,
    )

    synced_at = models.DateTimeField(
        auto_now=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-updated_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "name",
                    "language",
                ],
                name=(
                    "unique_whatsapp_template_language"
                ),
            )
        ]

    def __str__(self):
        return (
            f"{self.name} "
            f"({self.language})"
        )


# ============================================================
# Audience
# ============================================================

class Audience(models.Model):

    name = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return self.name


# ============================================================
# Audience Member
# ============================================================

class AudienceMember(models.Model):

    audience = models.ForeignKey(
        Audience,
        on_delete=models.CASCADE,
        related_name="members",
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="audiences",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "audience",
                    "customer",
                ],
                name=(
                    "unique_customer_per_audience"
                ),
            )
        ]

    def __str__(self):
        return (
            f"{self.audience.name} - "
            f"{self.customer}"
        )


# ============================================================
# Campaign
# ============================================================

class Campaign(models.Model):

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SCHEDULED", "Scheduled"),
        ("RUNNING", "Running"),
        ("PAUSED", "Paused"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
        ("FAILED", "Failed"),
    ]

    name = models.CharField(
        max_length=255,
    )

    template = models.ForeignKey(
        WhatsAppTemplate,
        on_delete=models.PROTECT,
        related_name="campaigns",
    )

    phone_number = models.ForeignKey(
        WhatsAppPhoneNumber,
        on_delete=models.PROTECT,
        related_name="campaigns",
    )

    # --------------------------------------------------------
    # Audience
    # --------------------------------------------------------

    audience = models.ForeignKey(
        Audience,
        on_delete=models.PROTECT,
        related_name="campaigns",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # --------------------------------------------------------
    # Campaign Statistics
    # --------------------------------------------------------

    total_recipients = models.PositiveIntegerField(
        default=0,
    )

    sent_count = models.PositiveIntegerField(
        default=0,
    )

    delivered_count = models.PositiveIntegerField(
        default=0,
    )

    read_count = models.PositiveIntegerField(
        default=0,
    )

    failed_count = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return self.name


# ============================================================
# Campaign Recipient
# ============================================================

class CampaignRecipient(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("QUEUED", "Queued"),
        ("SENDING", "Sending"),
        ("SENT", "Sent"),
        ("DELIVERED", "Delivered"),
        ("READ", "Read"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
    ]

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="recipients",
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="campaign_recipients",
    )

    phone = models.CharField(
        max_length=30,
    )

    variables = models.JSONField(
        default=dict,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    whatsapp_message_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_recipient",
    )

    queued_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "campaign",
                    "customer",
                ],
                name=(
                    "unique_customer_per_campaign"
                ),
            )
        ]

    def __str__(self):
        return (
            f"{self.campaign.name} - "
            f"{self.customer}"
        )

# ============================================================
# WhatsApp System Settings
# ============================================================

class WhatsAppSystemSettings(models.Model):
    """
    Global WhatsApp outbound sending configuration.

    There should only be one active settings record.
    """

    enabled = models.BooleanField(
        default=True,
        help_text=(
            "Enable or disable global WhatsApp "
            "outbound sending."
        ),
    )

    interval_seconds = models.PositiveIntegerField(
        default=15,
        help_text=(
            "Minimum number of seconds between "
            "outbound WhatsApp messages."
        ),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "WhatsApp System Settings"
        verbose_name_plural = "WhatsApp System Settings"

    def save(self, *args, **kwargs):
        """
        Enforce singleton behavior.

        ID is always forced to 1.
        """

        self.pk = 1

        super().save(
            *args,
            **kwargs,
        )

    def delete(self, *args, **kwargs):
        """
        Prevent deleting the global configuration.
        """

        return

    def __str__(self):
        return "WhatsApp System Settings"