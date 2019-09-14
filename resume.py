import json

from schemas import ensure_schema, ensure_logged_in_user

from config import RESUME, RESUME_BUCKET

import boto3
from botocore.exceptions import ClientError

def presign(method, event, ctx, user):
    client = boto3.client("s3", **RESUME)
    http_method = "GET"
    params = {
        "Bucket": RESUME_BUCKET,
        "Key": event["email"] + ".pdf"
    }
    if method == "put_object":
        http_method="PUT"
        params["ContentType"] = "application/pdf"
    return client.generate_presigned_url(
        method,
        Params=params,
        HttpMethod=http_method,
        ExpiresIn=3600,
    )


def exists(email):
    client = boto3.client("s3", **RESUME)
    try:
        info = client.head_object(Bucket=RESUME_BUCKET, Key=email + ".pdf")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise e
    
@ensure_schema({
    "type": "object",
    "properties": {
        "email": {"type": "string"},
        "token": {"type": "string"}
    },
    "required": ["email", "token"]
})
@ensure_logged_in_user()
def resume(event, ctx, user):
    try:
        return {
            "statusCode": 200, "body": {
                "upload": presign("put_object", event, ctx, user),
                "download": presign("get_object", event, ctx, user),
                "exists": exists(event["email"])
            }
        }
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": "failed to connect to s3" + str(e)
        }
    