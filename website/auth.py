import os

import aiohttp
from quart import Blueprint, redirect, request

from website.settings import settings

auth = Blueprint("auth", __name__)


@auth.route("/", methods=["POST"])
async def authenticate():
    form = await request.form
    phone_number = form.get("phone_number")
    auth_code = form.get("auth_code")

    payload = {
        "phone_number": phone_number,
        "auth_code": auth_code,
    }

    api_url = settings.TELEGRAM_API_URL

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url + "/verify", json=payload) as response:
            if response.status == 200:
                app_domain = request.host_url
                redirect_uri = (
                    app_domain.replace("http://", "https://")
                    + "auth/pipedrive/callback"
                )

                res = await response.json()
                pipedrive_client_id = res['pipedrive_client_id']  # get from database or sent it in response

                auth_url = (
                    f"https://oauth.pipedrive.com/oauth/authorize?client_id={pipedrive_client_id}&state"
                    f"=random_string&redirect_uri={redirect_uri}"
                )
                return redirect(auth_url)


@auth.route("/pipedrive")
async def pipedrive_login():
    print("Logging in")


@auth.route("/pipedrive/callback")
async def pipedrive_authorized():
    print("got a callback")
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
        "redirect_uri": "https://telegram-crm-plugin.herokuapp.com/auth/pipedrive/callback",
    }

    # Send the POST request to the URL
    response = requests.post(url, headers=header, data=body)
    if str(response.status_code)[0] == "4":
        print(response.json())

    else:
        print("Successfully posted authorization code")

    response_json = response.json()

    global access_token
    access_token = response_json["access_token"]
    refresh_token = response_json["refresh_token"]

    from urllib.parse import urlparse

    parsed_url = urlparse(response_json["api_domain"])
    domain_parts = parsed_url.netloc.split(".")
    company_domain = domain_parts[0]

    print("access_token", access_token)

    return redirect("/landing")
