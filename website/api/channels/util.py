import aiohttp
import logging


async def create_channel_PD(access_token, channel_id, name, provider_type="other"):
    request_options = {
        "url": "https://api.pipedrive.com/v1/channels",
        "method": "POST",
        "headers": {
            "Authorization": f"Bearer {access_token}",
        },
        "json": {
            "name": name,
            "provider_channel_id": channel_id,
            "provider_type": provider_type,
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            request_options["url"],
            headers=request_options["headers"],
            json=request_options["json"],
        ) as response:
            res = await response.json()
            logging.info(f"Response from Pipedrive for creating channel: {res}")
            return res['success'], response.status
