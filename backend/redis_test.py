import os
import asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from channels.layers import get_channel_layer


async def test_channel_layer():
    channel_layer = get_channel_layer()

    print("Channel layer:", channel_layer)

    channel_name = await channel_layer.new_channel()
    print("Channel:", channel_name)

    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "message": "Hello from Channels Redis",
        },
    )

    print("Message sent.")

    message = await channel_layer.receive(channel_name)

    print("Message received:", message)


asyncio.run(test_channel_layer())