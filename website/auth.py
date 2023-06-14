from datetime import datetime, timedelta
import logging
import base64
from urllib.parse import urlparse


import aiohttp
import quart
from quart import Blueprint, redirect, request, render_template

from website.settings import settings
from website.util import create_redirect_url
from website.connection import put_item, post

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

    response = await post(api_url + "create_string_1", json=payload)
    res = await response.json()
    
    if not res["success"]:
        return "Failed to authorize first time"

    payload = {"phone_number": phone_number}
    response = await post(api_url + "send_code_2", json=payload)
    res = await response.json()

    if not res["success"]:
        return "Failed to send code second time"
    
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
        # create the first session string
        async with session.post(api_url + "create_string_2", json=payload) as response:
            res = await response.json()
            if res["success"]:
                session = quart.session
                session["Logged In"] = True

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
        session["phone_number"],
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=date_expires.strftime("%Y-%m-%d %H:%M:%S"),
    )

    logging.info("Set access token for user " + str(session["phone_number"]))

    return redirect("/create_channel")


def create_authorization(client_id: str, client_secret: str):
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()

    return client_creds_b64


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

    response = await post(url, headers=header, data=body)
    response_data = await response.json()

    return response_data


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

    response = await post(url, headers=header, data=body)
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
