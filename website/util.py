import logging
from datetime import datetime, timezone

from website.settings import settings

import aiohttp
import quart


async def send_message_to_Telegram(recipient, msg):
    print("Sending message from Pipedrive to Telegram")

    # this is where we call our API
    api_url = settings.TELEGRAM_API_URL


async def send_message_to_PD(
    access_token: str,
    sender_id: str,
    channel_id: str,
    conversation_id: str,
    msg: str,
    time,
):

    url = "https://api.pipedrive.com/v1/channels/messages/receive"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    
    body = {
        "id": f"msg-te-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "channel_id": channel_id,
        "sender_id": sender_id,
        "conversation_id": conversation_id,
        "message": msg,
        "status": "sent",
        "created_at": time,
        "attachments": [],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            headers=headers,
            json=body,
        ) as response:
            status = response.status

            if status in [200, 201]:
                logging.info("Message sent successfully from Telegram to Pipedrive")
                return {"success": True}
        
            logging.info(f"Message failed to send from Telegram to Pipedrive with status {status} and response {await response.text()}")
            return {"success": False}


def create_redirect_url(session: quart.session):
    redirect_uri = settings.PIPEDRIVE_CALLBACK_URI

    pipedrive_client_id = session["pipedrive_client_id"]

    auth_url = (
        f"https://oauth.pipedrive.com/oauth/authorize?client_id={pipedrive_client_id}&state"
        f"=random_string&redirect_uri={redirect_uri}"
    )

    return auth_url
