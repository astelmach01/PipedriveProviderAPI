from datetime import datetime, timedelta
import logging
import base64
from urllib.parse import urlparse


import aiohttp
import quart
from quart import Blueprint, redirect, request, render_template

from website.settings import settings
from website.util import create_authorization, create_redirect_url
from website.connection import USER_ACCESS_KEYS, put_item

api_url = settings.TELEGRAM_API_URL

auth = Blueprint("auth", __name__)


@auth.route("/auth1", methods=["POST"])
async def auth1():
    form = await request.form
    phone_number = form.get("phone_number")
    phone_code_hash = form.get("phone_code_hash")
    auth_code = form.get("auth_code")

    payload = {
        "phone_number": phone_number,
        "phone_code_hash": phone_code_hash,
        "auth_code": auth_code,
    }

    # when we have received the phone number and auth code from the user
    async with aiohttp.ClientSession() as session:
        # create the first session string
        async with session.post(api_url + "create_string_1", json=payload) as response:
            res = await response.json()
            if res["success"]:
                payload = {"phone_number": phone_number}
                # create the second_session_string
                async with session.post(
                    api_url + "send_code_2", json=payload
                ) as response:
                    res = await response.json()
                    if res["success"]:
                        phone_code_hash = res["phone_code_hash"]
                        return await render_template(
                            "auth2.html",
                            phone_number=phone_number,
                            phone_code_hash=phone_code_hash,
                        )


@auth.route("/auth2", methods=["POST"])
async def auth2():
    form = await request.form
    phone_number = form.get("phone_number")
    phone_code_hash = form.get("phone_code_hash")
    auth_code = form.get("auth_code")

    payload = {
        "phone_number": phone_number,
        "phone_code_hash": phone_code_hash,
        "auth_code": auth_code,
    }

    # when we have received the phone number and auth code from the user
    async with aiohttp.ClientSession() as session:
        # create the first second string
        async with session.post(api_url + "create_string_2", json=payload) as response:
            res = await response.json()
            if res["success"]:
                session = quart.session
                session["Logged In"] = True

                pipedrive_client_id = session["pipedrive_client_id"]
                pipedrive_client_secret = session["pipedrive_client_secret"]

                put_item(
                    USER_ACCESS_KEYS,
                    phone_number,
                    pipedrive_client_id=pipedrive_client_id,
                    pipedrive_client_secret=pipedrive_client_secret,
                )

                return redirect(create_redirect_url(session))

            else:
                return "Failed to authorize second time"


@auth.route("/pipedrive")
async def pipedrive_login():
    print("Logging in")


@auth.route("/pipedrive/callback")
async def pipedrive_authorized():
    authorization_code = request.args.get("code")

    if not authorization_code:
        return "No authorization code received"

    session = quart.session
    client_id = session["pipedrive_client_id"]
    client_secret = session["pipedrive_client_secret"]

    response_json = await exchange_auth_code(
        authorization_code, client_id, client_secret
    )

    if "access_token" not in response_json:
        logging.info(response_json)
        return "Failed to get access token"

    access_token = response_json["access_token"]
    refresh_token = response_json["refresh_token"]
    expires_in = response_json[
        "expires_in"
    ]  # the maximum time in seconds until the access_token expires

    date_expires = datetime.now() + timedelta(seconds=expires_in)

    parsed_url = urlparse(response_json["api_domain"])
    domain_parts = parsed_url.netloc.split(".")
    company_domain = domain_parts[0]

    session["access_token"] = access_token
    session["refresh_token"] = refresh_token

    put_item(
        USER_ACCESS_KEYS,
        session["phone_number"],
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=date_expires.strftime("%Y-%m-%d %H:%M:%S"),
    )

    logging.info("Set access token for user " + str(session["phone_number"]))

    return redirect("/create_channel")


# step 4 of https://pipedrive.readme.io/docs/marketplace-oauth-authorization
async def exchange_auth_code(
    authorization_code: str, client_id: str, client_secret: str
) -> dict:
    client_creds_b64 = create_authorization(client_id, client_secret)

    url = "https://oauth.pipedrive.com/oauth/token"
    header = {
        "Authorization": f"Basic {client_creds_b64}",
    }

    body = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": settings.PIPEDRIVE_CALLBACK_URI,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=header, data=body) as response:
            response_data = await response.json()

    return response_data
