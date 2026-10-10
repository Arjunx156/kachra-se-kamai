import json
import os

import boto3
import pytest
from moto import mock_aws

TABLES = {
    "USERS_TABLE": ("t-users", [("userId", "S")], None, []),
    "SOCIETIES_TABLE": ("t-societies", [("societyId", "S")], None, []),
    "SCANS_TABLE": ("t-scans", [("userId", "S"), ("scanId", "S")], None, ["status-index", "society-index"]),
    "BUNDLES_TABLE": ("t-bundles", [("bundleId", "S")], None, ["status-index"]),
    "RATES_TABLE": ("t-rates", [("material", "S")], None, []),
    "STATS_TABLE": ("t-stats", [("scope", "S")], None, []),
}
GSI_KEYS = {"status-index": "status", "society-index": "societyId"}
BUCKET = "test-photos"
ADMIN_KEY = "test-admin-key"


def _create_table(ddb, name, keys, gsis):
    attrs = {k: t for k, t in keys}
    for g in gsis:
        attrs[GSI_KEYS[g]] = "S"
        attrs["createdAt"] = "S"
    params = {
        "TableName": name,
        "KeySchema": [{"AttributeName": k, "KeyType": "HASH" if i == 0 else "RANGE"} for i, (k, _) in enumerate(keys)],
        "AttributeDefinitions": [{"AttributeName": k, "AttributeType": t} for k, t in attrs.items()],
        "BillingMode": "PAY_PER_REQUEST",
    }
    if gsis:
        params["GlobalSecondaryIndexes"] = [
            {
                "IndexName": g,
                "KeySchema": [
                    {"AttributeName": GSI_KEYS[g], "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
            for g in gsis
        ]
    ddb.create_table(**params)


@pytest.fixture
def aws(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("PHOTO_BUCKET", BUCKET)
    monkeypatch.setenv("ADMIN_KEY", ADMIN_KEY)
    monkeypatch.setenv("MIN_BUNDLE_KG", "1.5")
    monkeypatch.setenv("TARGET_KG", "100")
    for env_name, (table_name, *_rest) in TABLES.items():
        monkeypatch.setenv(env_name, table_name)
    from lib import db

    with mock_aws():
        db.reset_clients()
        ddb = boto3.client("dynamodb", region_name="us-east-1")
        for table_name, keys, _unused, gsis in TABLES.values():
            _create_table(ddb, table_name, keys, gsis)
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket=BUCKET)
        yield
        db.reset_clients()


def call(handler, route_key, body=None, query=None, path=None, headers=None):
    """Invoke a Lambda handler with an HTTP API v2 event and decode the envelope."""
    event = {
        "routeKey": route_key,
        "body": json.dumps(body) if body is not None else None,
        "queryStringParameters": query,
        "pathParameters": path,
        "headers": headers or {},
    }
    resp = handler(event, None)
    return resp["statusCode"], json.loads(resp["body"])


@pytest.fixture
def seeded(aws):
    from handlers import admin

    status, body = call(admin.lambda_handler, "POST /admin/seed", headers={"x-admin-key": ADMIN_KEY})
    assert status == 200, body
    return body["data"]


os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
