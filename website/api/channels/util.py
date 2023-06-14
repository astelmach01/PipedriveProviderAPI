import logging

from website.connection import post


async def create_channel_PD(access_token, channel_id, name, provider_type="other"):
    
    url = "https://api.pipedrive.com/v1/channels"

    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    json = {
        "name": name,
        "provider_channel_id": channel_id,
        "provider_type": provider_type,
    }

    response = await post(url, headers=headers, json=json)
    res = await response.json()
    status = response.status
    logging.info(res)

    return status in [200, 201]
