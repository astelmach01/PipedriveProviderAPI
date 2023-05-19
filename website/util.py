from datetime import datetime, timezone
from settings import settings

import aiohttp


async def send_message_to_Telegram(recipient, msg):
    print("Sending message from Pipedrive to Telegram")

    # this is where we call our API
    api_url = settings.TELEGRAM_API_URL


async def send_message_to_PD(
    access_token: str, sender_id: str, channel_id: str, msg: str, time
):
    print("Sending message from Telegram to Pipedrive")

    created_at = time.strftime("%Y-%m-%d %H:%M")

    request_options = {
        "uri": "https://api.pipedrive.com/v1/channels/messages/receive",
        "method": "POST",
        "headers": {
            "Authorization": f"Bearer {access_token}",
        },
        "body": {
            "id": f"msg-te-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "channel_id": channel_id,
            "sender_id": sender_id,
            "conversation_id": f"conversation-{sender_id}",
            "message": msg,
            "status": "sent",
            "created_at": created_at,
            "attachments": [],
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            request_options["uri"],
            headers=request_options["headers"],
            json=request_options["body"],
        ) as response:
            status = str(response.status)[0]

            if status == "4" or status == "5":
                print("Error sending message from Telegram to Pipedrive")
                print(await response.json())
            else:
                print("Message sent successfully from Telegram to Pipedrive")
