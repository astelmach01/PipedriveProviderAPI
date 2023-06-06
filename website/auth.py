import os

import aiohttp
import requests
from quart import Blueprint, redirect, request, render_template, session

from website.settings import settings

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

    api_url = settings.TELEGRAM_API_URL

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

    api_url = settings.TELEGRAM_API_URL

    # when we have received the phone number and auth code from the user
    async with aiohttp.ClientSession() as session:
        # create the first session string
        async with session.post(api_url + "create_string_2", json=payload) as response:
            res = await response.json()
            if res["success"]:

                app_domain = request.host_url
                redirect_uri = (
                    app_domain.replace("http://", "https://")
                    + "auth/pipedrive/callback"
                )

                pipedrive_client_id = res["pipedrive_client_id"]

                auth_url = (
                    f"https://oauth.pipedrive.com/oauth/authorize?client_id={pipedrive_client_id}&state"
                    f"=random_string&redirect_uri={redirect_uri}"
                )
                return redirect(auth_url)

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

    url = "https://oauth.pipedrive.com/oauth/token"
    client_id = os.getenv("PIPEDRIVE_CLIENT_ID")
    client_secret = os.getenv("PIPEDRIVE_CLIENT_SECRET")

    import base64

    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()

    header = {
        "Authorization": f"Basic {client_creds_b64}",
    }

    body = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": "https://pipedrive-provider-api.herokuapp.com/auth/pipedrive/callback",
    }

    # Send the POST request to the URL
    response = requests.post(url, headers=header, data=body)
    if str(response.status_code)[0] == "4":
        print(response.json())

    else:
        print("Successfully posted authorization code")

    response_json = response.json()

    access_token = response_json["access_token"]
    refresh_token = response_json["refresh_token"]

    from urllib.parse import urlparse

    parsed_url = urlparse(response_json["api_domain"])
    domain_parts = parsed_url.netloc.split(".")
    company_domain = domain_parts[0]

    session['access_token'] = access_token

    print("access_token", access_token)

    return redirect("/create_channel")
