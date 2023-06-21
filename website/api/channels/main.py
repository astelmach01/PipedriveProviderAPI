import datetime
import logging
import aiohttp

from quart import Blueprint, request
from website.connection import USER_ACCESS_KEYS, get_access_token, get_attribute, get_phone_number

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
    url = settings.TELEGRAM_API_URL + "api/messages/send"
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
    channel_id = get_attribute(USER_ACCESS_KEYS, receiving_phone_number, "channel_id")

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
    messages_limit = request.args.get("messages_limit", default=0, type=int)
    if messages_limit == 0:
        messages_limit = None
        
    sender = get_phone_number(providerChannelId)
    conversation_id = sourceConversationId
    
    body = {
        "sender": sender,
        "conversation_id": conversation_id,
        "messages_limit": messages_limit,
    }

    # post to telegram API endpoint /api/conversations/getConversationById
    with aiohttp.ClientSession() as session:
        async with session.post(
            settings.TELEGRAM_API_URL + "api/conversations/getConversationById", json=body
        ) as response:
            res = await response.json()
            logging.info(f"Response from Telegram API: {res}")
            return res


# get conversations
@channels.route("/<providerChannelId>/conversations")
async def conversations(providerChannelId):
    
    conversations_limit = request.args.get("conversations_limit", default=10, type=int)
    messages_limit = request.args.get("messages_limit", default=10, type=int)
    
    body = {
        "conversations_limit": conversations_limit,
        "messages_limit": messages_limit,
    }
    
    # post to /api/conversations/getConversations
    with aiohttp.ClientSession() as session:
        async with session.post(
            settings.TELEGRAM_API_URL + "api/conversations/getConversations", json=body
        ) as response:
            res = await response.json()
            logging.info(f"Response from Telegram API: {res}")
            return res

    
