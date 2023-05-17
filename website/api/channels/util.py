import aiohttp


async def create_channel(access_token, id, name, provider_type="other"):
    request_options = {
        "url": "https://api.pipedrive.com/v1/channels",
        "method": "POST",
        "headers": {
            "Authorization": f"Bearer {access_token}",
        },
        "json": {
            "name": name,
            "provider_channel_id": id,
            "provider_type": provider_type,
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            request_options["url"],
            headers=request_options["headers"],
            json=request_options["json"],
        ) as response:
            status = str(response.status)[0]

            if status == "4" or status == "5":
                print("Error creating channel")
                return False
            else:
                print("Channel created successfully")
                return True
