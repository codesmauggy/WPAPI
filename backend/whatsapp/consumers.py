from channels.generic.websocket import AsyncJsonWebsocketConsumer


class DashboardConsumer(AsyncJsonWebsocketConsumer):
    group_name = "dashboard"

    async def connect(self):
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        await self.send_json(
            {
                "type": "connection.ready",
                "message": "WhatsApp dashboard WebSocket connected.",
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def dashboard_event(self, event):
        await self.send_json(event["data"])

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json(
                {
                    "type": "pong",
                    "message": "WebSocket receive is working.",
                }
            )