"""
Routes
"""
import json
import logging

import aiohttp
from quart import Blueprint, request, render_template

from website.api.channels.util import create_channel
from website.settings import settings

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

        api_url = settings.TELEGRAM_API_URL

        logging.info("Sending sync")

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
async def _create_channel(access_token: str):
    if request.method == "POST":
        form = await request.form
        channel_id = form.get("channel_id")
        provider_type = form.get("provider_type", "other")
        channel_name = form.get("channel_name")

        success = await create_channel(
            access_token, channel_id, channel_name, provider_type
        )

        if success:
            return await render_template("success.html")
        else:
            return await render_template("error.html")

    return await render_template("create_channel.html")
