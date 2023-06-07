import logging
import base64
from urllib.parse import urlencode

import aiohttp
import quart
from quart import Blueprint, redirect, request, render_template

from website.settings import settings
from website.util import create_redirect_url

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
    url = "https://oauth.pipedrive.com/oauth/token"
    client_id = session["pipedrive_client_id"]
    client_secret = session["pipedrive_client_secret"]

    response_json = await exchange_auth_code(
        authorization_code, url, client_id, client_secret
    )

    if "access_token" not in response_json:
        logging.info(response_json)
        return "Failed to get access token"

    access_token = response_json["access_token"]
    refresh_token = response_json["refresh_token"]
    expires_in = response_json[
        "expires_in"
    ]  # the maximum time in seconds until the access_token expires

    from urllib.parse import urlparse

    parsed_url = urlparse(response_json["api_domain"])
    domain_parts = parsed_url.netloc.split(".")
    company_domain = domain_parts[0]

    session["access_token"] = access_token
    session["refresh_token"] = refresh_token

    print("access_token", access_token)

    return redirect("/create_channel")


# step 4 of https://pipedrive.readme.io/docs/marketplace-oauth-authorization
async def exchange_auth_code(
    authorization_code: str, url: str, client_id: str, client_secret: str
) -> dict:
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()

    header = {
        "Authorization": f"Basic {client_creds_b64}",
    }

    body = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": settings.PIPEDRIVE_CALLBACK_URI,
    }

    encoded_body = urlencode(body)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=header, data=encoded_body) as response:
            response_data = await response.json()

    return response_data



