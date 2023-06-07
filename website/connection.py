import logging
import boto3
from website.settings import settings

client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name="us-east-2",
)


def put_item(phone_number: str, **kwargs):
    item = {"phone-number": {"S": phone_number}}

    # Add the kwargs to the item dictionary
    for key, value in kwargs.items():
        item[key] = {"S": str(value)}

    logging.info(f"Putting item {item} into table {settings.TABLE_NAME}")
    response = client.put_item(TableName=settings.TABLE_NAME, Item=item)
    return response["ResponseMetadata"]["HTTPStatusCode"] == 200


def get_attribute(phone_number: str, attribute: str):
    logging.info(f"Getting attribute '{attribute}' for phone number '{phone_number}'")
    response = client.get_item(
        TableName=settings.TABLE_NAME, Key={"phone-number": {"S": phone_number}}
    )
    item = response.get("Item")
    if item is not None:
        return item.get(attribute, {}).get("S")
    else:
        return None


def delete_item(phone_number: str):
    logging.info(f"Deleting item for phone number {phone_number}")
    response = client.delete_item(
        TableName=settings.TABLE_NAME, Key={"phone-number": {"S": phone_number}}
    )
    return response["ResponseMetadata"]["HTTPStatusCode"] == 200


# convenience function
def put_access_key(phone_number: str, access_key: str):
    return put_item(phone_number, access_key=access_key)


def get_access_key(phone_number: str):
    return get_attribute(phone_number, "access_key")