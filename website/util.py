import base64
import logging
from datetime import datetime, timezone, timedelta
from website.connection import put_item, get_attribute

from website.settings import settings

import quart
import aiohttp


def create_authorization(client_id: str, client_secret: str):
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()

    return client_creds_b64


async def refresh_token(
    phone_number: str, client_id: str, client_secret: str, refresh_token: str
) -> str:
    url = "https://oauth.pipedrive.com/oauth/token"
    client_creds_b64 = create_authorization(client_id, client_secret)

    header = {
        "Authorization": f"Basic {client_creds_b64}",
    }

    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=header, data=body) as response:
            response_data = await response.json()

    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    expires_in = response_data["expires_in"]

    date_expires = datetime.now() + timedelta(seconds=expires_in)

    put_item(
        phone_number,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=date_expires.strftime("%Y-%m-%d %H:%M:%S"),
    )

    return access_token


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
    receiving_phone_number: str,
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

        # refresh the access token if it's expired
        token = await refresh_token(
            receiving_phone_number,
            get_attribute(receiving_phone_number, "pipedrive_client_id"),
            get_attribute(receiving_phone_number, "pipedrive_client_secret"),
            get_attribute(receiving_phone_number, "refresh_token"),
        )

        headers = {
            "Authorization": f"Bearer {token}",
        }

        async with session.post(
            url,
            headers=headers,
            json=body,
        ) as response:
            status = response.status

            if status in [200, 201]:
                logging.info("Message sent successfully from Telegram to Pipedrive")
                return {"success": True}

            logging.info(
                f"Message failed to send from Telegram to Pipedrive with status {status} and response {await response.text()}"
            )
            return {"success": False}


def create_redirect_url(session: quart.session):
    redirect_uri = settings.PIPEDRIVE_CALLBACK_URI

    pipedrive_client_id = session["pipedrive_client_id"]

    auth_url = (
        f"https://oauth.pipedrive.com/oauth/authorize?client_id={pipedrive_client_id}&state"
        f"=random_string&redirect_uri={redirect_uri}"
    )

    return auth_url
