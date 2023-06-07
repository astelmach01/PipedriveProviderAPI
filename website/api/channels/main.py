import logging
from datetime import datetime, timezone

import aiohttp
from quart import Blueprint, request, render_template

from website.util import send_message_to_Telegram

channels = Blueprint("channels", __name__)


# Get sender by ID
@channels.route("/<providerChannelId>/senders/<senderId>")
async def sender(providerChannelId, senderId):
    # make a call to our Telegram API here
    return {"success": True, "data": {"id": str(senderId)}}


# Post message from pipedrive to Telegram
@channels.route("/<providerChannelId>/messages", methods=["POST"])
async def messages(providerChannelId):
    print("Incoming message from pipedrive")

    # post to telegram API

    # Get the multipart form data
    data = await request.form
    data = data.to_dict()

    message = data["message"]
    recipient = data["recipientIds[]"]
    recipient = "+" + recipient

    message_id = "msg-pd-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    if await send_message_to_Telegram(recipient, message):
        return {"success": True, "data": {"id": message_id}}

    else:
        return {"success": False, "data": {"id": message_id}}


# from telegram to pipedrive
@channels.route("/messages/receive", methods=["POST"])
async def receive_message():
    data = await request.get_json()

    msg = data["msg"]
    receiving_phone_number = data["receiving_phone_number"]
    time = data["time"]
    sender_id = data["sender_id"]
    conversation_id = data["conversation_id"]

    # database call here
    access_token = access_tokens[receiving_phone_number]
    channel_id = channel_ids[receiving_phone_number]

    response = await send_message_to_PD(
        access_token, sender_id, channel_id, msg, time, conversation_id
    )
    logging.info(response)

    return response


# Get conversation by ID
@channels.route("/<providerChannelId>/conversations/<sourceConversationId>")
async def get_convo_by_id(providerChannelId, sourceConversationId):
    # forward to telegram API here

    fake_response = {
        "success": True,
        "data": {
            "id": f"{sourceConversationId}",
            "link": f"https://example.com/{providerChannelId}/{sourceConversationId}",
            "status": "open",
            "seen": True,
            "next_messages_cursor": "c-next",
            "messages": [],
            "participants": [
                {
                    "id": "sender-pd-1",
                    "name": f"Pipedriver Bot",
                    "role": "source_user",
                    "avatar_url": "https://www.gravatar.com/avatar/205e460b479e2e5b48aec07710c08d50",
                },
                {
                    "id": sourceConversationId.split("-")[1],
                    "name": f"Telegramer Bot 2",
                    "role": "end_user",
                    "avatar_url": "https://www.gravatar.com/avatar/205e460b479e2e5b48aec07710c08d50",
                },
            ],
        },
        "additional_data": {
            "after": None,
        },
    }
    print(fake_response)
    return fake_response


# get conversations
@channels.route("/<providerChannelId>/conversations")
async def conversations(providerChannelId):
    print("getting conversations")
    conversations_limit = request.args.get("conversations_limit", default=10, type=int)
    messages_limit = request.args.get("messages_limit", default=10, type=int)
    after = request.args.get("after")

    me = {
        "id": "me",
        "name": "Me",
        "role": "end_user",
        "avatar_url": "https://robohash.org/mxtouwlpxqjqtxiltdui?set=set1&bgset=&size=48x48",
    }
    participants_list = [me, me]

    fake_response = {
        "success": True,
        "data": [
            {
                "id": "conversation-5203254821",
                "link": "www.example.com",
                "status": "open",
                "seen": True,
                "next_messages_cursor": None,
                "messages": [],
                "participants": participants_list,
            }
        ],
        "additional_data": {
            "after": "c-next",
        },
    }

    return fake_response


async def send_message_to_PD(
    access_token: str,
    sender_id: str,
    channel_id: str,
    msg: str,
    time,
    conversation_id: str,
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
            "conversation_id": conversation_id,
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
            res = await response.json()
            logging.info(res)
            return res
