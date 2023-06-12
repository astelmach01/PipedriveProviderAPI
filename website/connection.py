import logging
import boto3
from website.settings import settings

client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name="us-east-2",
)


def get_update_params(body):
    """Given a dictionary we generate an update expression and a dict of values
    to update a dynamodb table.

    Params:
        body (dict): Parameters to use for formatting.

    Returns:
        update expression, dict of values.
    """
    update_expression = ["set "]
    update_values = dict()

    for key, val in body.items():
        update_expression.append(f" {key} = :{key},")
        update_values[f":{key}"] = val

    return "".join(update_expression)[:-1], update_values


def put_item(phone_number: str, **kwargs):
    a, v = get_update_params(kwargs)
    logging.info(
        f"Putting item for phone number {phone_number} with values {v} and expression {a}"
    )
    response = client.update_item(
        Key={"phone-number": phone_number},
        UpdateExpression=a,
        ExpressionAttributeValues=dict(v),
    )
    return response


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


if __name__ == "__main__":
    put_item("1234567890", access_key="1234")
