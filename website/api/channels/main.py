import datetime
import logging
import aiohttp

from quart import Blueprint, request
from website.connection import get_access_token, get_attribute

from website.util import send_message_to_PD
from website.settings import settings

channels = Blueprint("channels", __name__)


# Get sender by ID
@channels.route("/<providerChannelId>/senders/<senderId>")
async def sender(providerChannelId, senderId):
    # make a call to our Telegram API here
    return {"success": True, "data": {"id": str(senderId)}}


# Post message from pipedrive to Telegram 
# this function is called when you (not the person you are messaging) send a message
@channels.route("/<providerChannelId>/messages", methods=["POST"])
async def messages(providerChannelId):
    print("Incoming message from pipedrive")

    # Get the multipart form data
    data = await request.form
    now = datetime.datetime.now()
    url = settings.TELEGRAM_API_URL + "api/channels/messages"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            res = await response.json()
            logging.info(f"Response from Telegram API: {res}") 
            return res


# from telegram to pipedrive
# this function is called when the person you are messaging sends a message
@channels.route("/messages/receive", methods=["POST"])
async def receive_message():
    data = await request.get_json()

    msg = data["msg"]
    receiving_phone_number = data["receiving_phone_number"]
    time = data["time"]
    sender_id = data["sender_id"]
    conversation_id = data["conversation_id"]

    # database call here
    access_token = get_access_token(receiving_phone_number)
    channel_id = get_attribute(receiving_phone_number, "channel_id")

    response = await send_message_to_PD(
        access_token,
        sender_id,
        channel_id,
        conversation_id,
        msg,
        time,
        receiving_phone_number,
    )

    logging.info(f"Response from Pipedrive: {response}")
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
                    "id": sourceConversationId,
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
