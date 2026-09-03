import time

from django.core.cache import cache

from .models import WhatsAppSystemSettings


# ============================================================
# Redis Keys
# ============================================================

RATE_LIMIT_KEY = (
    "whatsapp:global:last_reserved_send"
)

RATE_LOCK_KEY = (
    "whatsapp:global:send_lock"
)


# ============================================================
# Configuration
# ============================================================

LOCK_TIMEOUT = 10

KEY_TIMEOUT = 60 * 60 * 24


# ============================================================
# Get Global WhatsApp Settings
# ============================================================

def get_sending_settings():
    """
    Get the single global WhatsApp sending configuration.

    If the configuration does not exist, create it with
    safe default values.
    """

    settings, _ = (
        WhatsAppSystemSettings.objects
        .get_or_create(
            pk=1,
            defaults={
                "enabled": True,
                "interval_seconds": 15,
            },
        )
    )

    return settings


# ============================================================
# Reserve Global Sending Slot
# ============================================================

def reserve_send_slot():
    """
    Reserve the next global WhatsApp sending slot.

    Returns:
        float:
            Number of seconds until this recipient is allowed
            to send.

    Example with 20-second interval:

        First recipient  -> 0 seconds
        Second recipient -> ~20 seconds
        Third recipient  -> ~40 seconds
        Fourth recipient -> ~60 seconds

    Redis locking ensures multiple Celery workers share
    the same global sending clock.
    """

    settings = get_sending_settings()

    # --------------------------------------------------------
    # Global outbound sending disabled
    # --------------------------------------------------------

    if not settings.enabled:
        return 0.0

    # --------------------------------------------------------
    # Protect against invalid values
    # --------------------------------------------------------

    interval = max(
        1,
        int(
            settings.interval_seconds
        ),
    )

    # --------------------------------------------------------
    # Acquire distributed Redis lock
    # --------------------------------------------------------

    lock = cache.lock(
        RATE_LOCK_KEY,
        timeout=LOCK_TIMEOUT,
        blocking_timeout=LOCK_TIMEOUT,
    )

    acquired = False

    try:

        acquired = lock.acquire(
            blocking=True
        )

        if not acquired:

            raise RuntimeError(
                "Unable to acquire WhatsApp "
                "global sending lock."
            )

        # ----------------------------------------------------
        # Current time
        # ----------------------------------------------------

        now = time.time()

        # ----------------------------------------------------
        # Get last reserved sending slot
        # ----------------------------------------------------

        last_reserved = cache.get(
            RATE_LIMIT_KEY
        )

        # ----------------------------------------------------
        # First message
        # ----------------------------------------------------

        if last_reserved is None:

            next_send_at = now

        # ----------------------------------------------------
        # Subsequent messages
        # ----------------------------------------------------

        else:

            last_reserved = float(
                last_reserved
            )

            next_send_at = max(
                now,
                last_reserved + interval,
            )

        # ----------------------------------------------------
        # Calculate delay
        # ----------------------------------------------------

        delay = max(
            0.0,
            next_send_at - now,
        )

        # ----------------------------------------------------
        # Reserve this slot
        # ----------------------------------------------------

        cache.set(
            RATE_LIMIT_KEY,
            next_send_at,
            timeout=KEY_TIMEOUT,
        )

        return delay

    finally:

        if acquired:
            lock.release()


# ============================================================
# Reset Global Rate Limiter
# ============================================================

def reset_rate_limiter():
    """
    Reset the global sending clock.

    Useful for development/testing.

    This does NOT modify the global sending settings.
    """

    cache.delete(
        RATE_LIMIT_KEY
    )