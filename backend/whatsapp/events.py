from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_dashboard_event(data: dict):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "dashboard",
        {
            "type": "dashboard.event",
            "data": data,
        },
    )

def broadcast_customer_created(customer):
    broadcast_dashboard_event({
        "type": "customer.created",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "whatsapp_id": customer.whatsapp_id,
            "marketing_opted_in": customer.marketing_opted_in,
            "marketing_opted_in_at": (
                customer.marketing_opted_in_at.isoformat()
                if customer.marketing_opted_in_at
                else None
            ),
            "marketing_opted_out_at": (
                customer.marketing_opted_out_at.isoformat()
                if customer.marketing_opted_out_at
                else None
            ),
            "tags": customer.tags,
            "custom_fields": customer.custom_fields,
            "last_message_at": (
                customer.last_message_at.isoformat()
                if customer.last_message_at
                else None
            ),
            "is_active": customer.is_active,
            "status": customer.status,
            "created_at": (
                customer.created_at.isoformat()
                if customer.created_at
                else None
            ),
            "updated_at": (
                customer.updated_at.isoformat()
                if customer.updated_at
                else None
            ),
        },
    })


def broadcast_customer_updated(customer):
    broadcast_dashboard_event({
        "type": "customer.updated",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "whatsapp_id": customer.whatsapp_id,
            "marketing_opted_in": customer.marketing_opted_in,
            "marketing_opted_in_at": (
                customer.marketing_opted_in_at.isoformat()
                if customer.marketing_opted_in_at
                else None
            ),
            "marketing_opted_out_at": (
                customer.marketing_opted_out_at.isoformat()
                if customer.marketing_opted_out_at
                else None
            ),
            "tags": customer.tags,
            "custom_fields": customer.custom_fields,
            "last_message_at": (
                customer.last_message_at.isoformat()
                if customer.last_message_at
                else None
            ),
            "is_active": customer.is_active,
            "status": customer.status,
            "created_at": (
                customer.created_at.isoformat()
                if customer.created_at
                else None
            ),
            "updated_at": (
                customer.updated_at.isoformat()
                if customer.updated_at
                else None
            ),
        },
    })

# ============================================================
# AUDIENCE REALTIME EVENTS
# ============================================================

def _audience_payload(audience):
    return {
        "id": audience.id,
        "name": audience.name,
        "description": audience.description,
        "is_active": audience.is_active,
        "member_count": audience.members.count(),
        "created_at": (
            audience.created_at.isoformat()
            if audience.created_at
            else None
        ),
        "updated_at": (
            audience.updated_at.isoformat()
            if audience.updated_at
            else None
        ),
    }


def _audience_customer_payload(customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "whatsapp_id": customer.whatsapp_id,
        "marketing_opted_in": customer.marketing_opted_in,
        "marketing_opted_in_at": (
            customer.marketing_opted_in_at.isoformat()
            if customer.marketing_opted_in_at
            else None
        ),
        "is_active": customer.is_active,
        "status": customer.status,
    }


def broadcast_audience_created(audience):
    broadcast_dashboard_event({
        "type": "audience.created",
        "audience": _audience_payload(audience),
    })


def broadcast_audience_updated(audience):
    broadcast_dashboard_event({
        "type": "audience.updated",
        "audience": _audience_payload(audience),
    })


def broadcast_audience_deleted(
    audience_id,
    name,
):
    broadcast_dashboard_event({
        "type": "audience.deleted",
        "audience_id": audience_id,
        "audience": {
            "id": audience_id,
            "name": name,
        },
    })


def broadcast_audience_membership_updated(
    audience,
    action,
    customer=None,
    customer_id=None,
):
    broadcast_dashboard_event({
        "type": "audience.membership.updated",
        "audience_id": audience.id,
        "action": action,
        "audience": _audience_payload(audience),
        "customer": (
            _audience_customer_payload(customer)
            if customer
            else None
        ),
        "customer_id": (
            customer.id
            if customer
            else customer_id
        ),
    })