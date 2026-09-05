from django.urls import path

from .views import whatsapp_webhook

from .api.api import (
    campaign_list,
    campaign_options,
    create_campaign,
    campaign_preview,
    generate_recipients,
    queue_campaign_api,
    campaign_status,
    campaign_recipients,
    pause_campaign,
    resume_campaign,
    cancel_campaign,
)

from .api.customer_api import (
    customer_list,
    customer_detail,
)

from .api.conversation_api import (
    conversation_list,
    conversation_detail,
    conversation_messages,
)

from .api.message_api import (
    message_list,
    message_detail,
    message_create,
)

from .api.send_api import (
    send_conversation_message,
)

urlpatterns = [
    # ========================================================
    # WhatsApp Webhook
    # ========================================================

    path(
        "webhook/",
        whatsapp_webhook,
        name="whatsapp-webhook",
    ),

    # ========================================================
    # Customers
    # ========================================================

    path(
        "customers/",
        customer_list,
        name="customer-list",
    ),

    path(
        "customers/<int:customer_id>/",
        customer_detail,
        name="customer-detail",
    ),

    # ========================================================
    # Conversations
    # ========================================================

    path(
        "conversations/",
        conversation_list,
        name="conversation-list",
    ),

    path(
        "conversations/<int:conversation_id>/",
        conversation_detail,
        name="conversation-detail",
    ),

    path(
        "conversations/<int:conversation_id>/send/",
        send_conversation_message,
        name="conversation-send",
    ),

    path(
        "conversations/<int:conversation_id>/messages/",
        message_list,
        name="message-list",
    ),

    # ========================================================
    # Messages
    # ========================================================

    path(
        "conversations/<int:conversation_id>/messages/create/",
        message_create,
        name="message-create",
    ),

    path(
        "messages/<int:message_id>/",
        message_detail,
        name="message-detail",
    ),

    # ========================================================
    # Campaign
    # ========================================================

    path(
        "campaigns/",
        campaign_list,
        name="campaign-list",
    ),

    path(
        "campaigns/options/",
        campaign_options,
        name="campaign-options",
    ),

    path(
        "campaigns/create/",
        create_campaign,
        name="campaign-create",
    ),


    # ========================================================
    # Campaign Preview
    # ========================================================

    path(
        "campaigns/<int:campaign_id>/preview/",
        campaign_preview,
        name="campaign-preview",
    ),

    # ========================================================
    # Generate Recipients
    # ========================================================

    path(
        "campaigns/<int:campaign_id>/generate-recipients/",
        generate_recipients,
        name="generate-campaign-recipients",
    ),

    # ========================================================
    # Campaign Recipients
    # ========================================================

    path(
        "campaigns/<int:campaign_id>/recipients/",
        campaign_recipients,
        name="campaign-recipients",
    ),

    # ========================================================
    # Queue
    # ========================================================

    path(
        "campaigns/<int:campaign_id>/queue/",
        queue_campaign_api,
        name="queue-campaign",
    ),

    # ========================================================
    # Status
    # ========================================================

    path(
        "campaigns/<int:campaign_id>/status/",
        campaign_status,
        name="campaign-status",
    ),

    # ========================================================
    # Pause
    # ========================================================

    path(
        "campaigns/<int:campaign_id>/pause/",
        pause_campaign,
        name="pause-campaign",
    ),

    # ========================================================
    # Resume
    # ========================================================

    path(
        "campaigns/<int:campaign_id>/resume/",
        resume_campaign,
        name="resume-campaign",
    ),

    # ========================================================
    # Cancel
    # ========================================================

    path(
        "campaigns/<int:campaign_id>/cancel/",
        cancel_campaign,
        name="cancel-campaign",
    ),
]