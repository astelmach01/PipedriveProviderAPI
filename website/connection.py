import logging
import boto3
from website.settings import settings

client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name="us-east-2",
)

USER_ACCESS_KEYS = "user-access-keys"
CHANNEL_ID_TO_PHONE_NUMBER = "channel_id-to-phone_number"

def make_key(table_name: str, key: str):
    if table_name == USER_ACCESS_KEYS:
        return {"phone-number": {"S": key}}
    
    elif table_name == CHANNEL_ID_TO_PHONE_NUMBER:
        return {"channel_id": {"S": key}}


def put_item(table_name: str, key: str, **kwargs):
    item = dict()

    for key, value in kwargs.items():
        item[key] = {"Value": {"S": str(value)}, "Action": "PUT"}

    logging.info(f"Putting item {item} with key {key}")
    response = client.update_item(
        TableName=table_name,
        Key=make_key(table_name, key),
        AttributeUpdates=item,
    )
    return response["ResponseMetadata"]["HTTPStatusCode"] == 200


def get_attribute(table_name: str, key: str, attribute: str):
    logging.info(f"Getting attribute '{attribute}' for key '{key}'")
    response = client.get_item(
        TableName=table_name, Key=make_key(table_name, key)
    )
    item = response.get("Item")
    if item is not None:
        return item.get(attribute, {}).get("S")
    else:
        return None


def delete_item(table_name: str, key: str):
    logging.info(f"Deleting item {key}")
    response = client.delete_item(
        TableName=table_name, Key=make_key(table_name, key)
    )
    return response["ResponseMetadata"]["HTTPStatusCode"] == 200


# convenience function
def put_access_key(phone_number: str, access_key: str):
    return put_item(USER_ACCESS_KEYS, key=phone_number, access_key=access_key)


def get_access_token(phone_number: str):
    return get_attribute(USER_ACCESS_KEYS, key=phone_number, attribute="access_token")

def put_channel_id(channel_id: str, phone_number: str):
    return put_item(CHANNEL_ID_TO_PHONE_NUMBER, key=channel_id, phone_number=phone_number)

def get_phone_number(channel_id: str):
    return get_attribute(CHANNEL_ID_TO_PHONE_NUMBER, key=channel_id, attribute="phone_number")
