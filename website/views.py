"""
Routes
"""
import logging
import aiohttp

import quart
from quart import Blueprint, redirect, request, render_template

from website.api.channels.util import create_channel_PD
from website.settings import settings
from website.util import create_redirect_url, refresh_token
from website.connection import USER_ACCESS_KEYS, get_attribute, put_channel_id, put_item

views = Blueprint("views", __name__)


@views.route("/", methods=["GET", "POST"])
async def send_code():
    if request.method == "POST":
        form = await request.form
        phone_number = form.get("phone_number")
        telegram_api_id = form.get("telegram_api_id")
        telegram_api_hash = form.get("telegram_api_hash")
        pipedrive_client_id = form.get("pipedrive_client_id")
        pipedrive_client_secret = form.get("pipedrive_client_secret")

        # Prepare the payload for the request to the Telegram API
        payload = {
            "phone_number": phone_number,
            "telegram_api_id": telegram_api_id,
            "telegram_api_hash": telegram_api_hash,
            "pipedrive_client_id": pipedrive_client_id,
            "pipedrive_client_secret": pipedrive_client_secret,
        }

        session = quart.session

        if "Logged In" in session and session["Logged In"]:
            return redirect(create_redirect_url(session))

        session["phone_number"] = phone_number
        session["pipedrive_client_id"] = pipedrive_client_id
        session["pipedrive_client_secret"] = pipedrive_client_secret

        api_url = settings.TELEGRAM_API_URL

        # for session stickiness
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url + "sync", json=payload) as response:
                res = await response.json()
                logging.info(res)

        async with aiohttp.ClientSession() as session:
            async with session.post(api_url + "send_code_1", json=payload) as response:
                res = await response.json()
                logging.info(res)
                if res["success"]:
                    phone_code_hash = res["phone_code_hash"]
                    return await render_template(
                        "auth1.html",
                        phone_number=phone_number,
                        phone_code_hash=phone_code_hash,
                    )

                else:
                    # Request failed, handle the error
                    return "Failed to call Telegram API"

    else:
        return await render_template("base.html")


@views.route("/create_channel", methods=["GET", "POST"])
async def create_channel():
    
    if request.method == "GET":
        return await render_template("create_channel.html")
    
    form = await request.form
    channel_id = form.get("channel_id")
    provider_type = form.get("provider_type", "other")
    channel_name = form.get("channel_name")
    
    session = quart.session
    put_item(USER_ACCESS_KEYS, session["phone_number"], channel_id=channel_id)
    put_channel_id(channel_id, session["phone_number"])

    session = quart.session
    access_token = session["access_token"]

    success, response_code = await create_channel_PD(
        access_token, channel_id, channel_name, provider_type
    )

    if success:
        return await render_template("success.html")
    
    if not success and response_code != 401:
        put_item(USER_ACCESS_KEYS, session["phone_number"], channel_id=None)
        put_channel_id(channel_id, None)
        return await render_template("error.html")
    
    # If the channel creation failed, try to refresh the token and try again
    token = get_attribute(USER_ACCESS_KEYS, session["phone_number"], "refresh_token")
    access_token = await refresh_token(session["phone_number"], session["pipedrive_client_id"], session["pipedrive_client_secret"], token)
    
    success, response_code = await create_channel_PD(
        access_token, channel_id, channel_name, provider_type
    )
    
    if success:
        return await render_template("success.html")
    
    
    put_item(USER_ACCESS_KEYS, session["phone_number"], channel_id=None)
    put_channel_id(channel_id, None)
    return await render_template("error.html")

