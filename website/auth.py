import os

from quart import Blueprint, redirect, render_template, request

auth = Blueprint("auth", __name__)


@auth.route("/", methods=["POST"])
async def authenticate():
    form = await request.form
    phone_number = form.get("phone")
    phone_code_hash = form.get("phone_code_hash")
    phone_code = form.get("code")

    print(phone_number, phone_code_hash, phone_code)

    try:
        await client.sign_in(phone_number, phone_code_hash, phone_code)
        await client.disconnect()
        await client.start()
        auth_url = f"https://oauth.pipedrive.com/oauth/authorize?client_id={pipedrive_client_id}&state=random_string&redirect_uri={redirect_uri}"

        return redirect(auth_url)

    except BadRequest as e:
        return f"An error occurred: {e}"
    except SessionPasswordNeeded:
        # Handle two-factor authentication
        return await render_template("two_factor_auth.html")


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
