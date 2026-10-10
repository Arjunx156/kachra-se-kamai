"""Local preview server: runs the real Lambda handlers against moto (mock DynamoDB + S3).

LOCAL PREVIEW ONLY. Not deployed. Without AWS credentials there is no Bedrock, so:
  - bin scans return the sample model reply in tests/fixtures/mixed_bin.json (clearly labelled),
  - the coach returns a notice instead of calling the agent.

Usage:  .venv/Scripts/python local/server.py     then set VITE_API_URL=http://localhost:8787
"""
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

MOTO_PORT = 5001
API_PORT = 8787
TABLES = {
    "USERS_TABLE": ("local-users", [("userId", "S")], []),
    "SOCIETIES_TABLE": ("local-societies", [("societyId", "S")], []),
    "SCANS_TABLE": ("local-scans", [("userId", "S"), ("scanId", "S")], ["status-index", "society-index"]),
    "BUNDLES_TABLE": ("local-bundles", [("bundleId", "S")], ["status-index"]),
    "RATES_TABLE": ("local-rates", [("material", "S")], []),
    "STATS_TABLE": ("local-stats", [("scope", "S")], []),
}
GSI_KEYS = {"status-index": "status", "society-index": "societyId"}
BUCKET = "local-photos"

os.environ.update(
    {
        "AWS_ACCESS_KEY_ID": "local",
        "AWS_SECRET_ACCESS_KEY": "local",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_REGION": "us-east-1",
        "AWS_ENDPOINT_URL": f"http://127.0.0.1:{MOTO_PORT}",
        "PHOTO_BUCKET": BUCKET,
        "ADMIN_KEY": "local-admin-key",
        **{k: v[0] for k, v in TABLES.items()},
    }
)

import boto3  # noqa: E402
from moto.server import ThreadedMotoServer  # noqa: E402

from handlers import admin, bundles, coach, rates, scans, stats, uploads, users  # noqa: E402
from lib import http as lib_http  # noqa: E402
from lib import seed, vision  # noqa: E402

ROUTES = [
    ("GET", "/health", stats), ("GET", "/stats/city", stats), ("GET", "/leaderboard", stats),
    ("POST", "/users", users), ("GET", "/me", users),
    ("POST", "/uploads", uploads),
    ("POST", "/scans", scans), ("GET", "/scans", scans), ("GET", "/scans/{scanId}", scans),
    ("POST", "/bundles/build", bundles), ("GET", "/bundles", bundles), ("GET", "/bundles/{bundleId}", bundles),
    ("POST", "/bundles/{bundleId}/accept", bundles), ("POST", "/bundles/{bundleId}/collect", bundles),
    ("GET", "/rates", rates), ("PUT", "/rates/{material}", rates),
    ("POST", "/coach", coach),
    ("POST", "/admin/seed", admin), ("POST", "/admin/reset", admin),
]


def _compile(template: str) -> re.Pattern:
    return re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", template) + "$")


COMPILED = [(m, t, _compile(t), mod) for m, t, mod in ROUTES]


class FixtureBedrock:
    """LOCAL PREVIEW: stands in for Bedrock with the sample reply from the test fixtures."""

    def converse(self, **_kwargs):
        text = (ROOT / "tests" / "fixtures" / "mixed_bin.json").read_text(encoding="utf-8")
        data = json.loads(text)
        data["tip"] = "[Local preview: sample AI reply, Bedrock not connected] " + data["tip"]
        return {"output": {"message": {"content": [{"text": json.dumps(data)}]}}}


def _local_coach(_user_id: str, language: str) -> tuple[str, list[str]]:
    msg = {
        "en": "Local preview: the Kamai Coach runs a Strands agent on Amazon Bedrock, which isn't connected on this machine. Deploy to AWS to see a real plan.",
        "hi": "Local preview: Kamai Coach ko Amazon Bedrock chahiye, jo is machine par connected nahi hai. Asli plan ke liye AWS par deploy kijiye.",
    }
    return msg.get(language, msg["en"]), []


def setup_aws() -> None:
    ddb = boto3.client("dynamodb")
    for name, keys, gsis in TABLES.values():
        attrs = dict(keys)
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
                    "KeySchema": [{"AttributeName": GSI_KEYS[g], "KeyType": "HASH"}, {"AttributeName": "createdAt", "KeyType": "RANGE"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
                for g in gsis
            ]
        ddb.create_table(**params)
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket=BUCKET)
    s3.put_bucket_cors(
        Bucket=BUCKET,
        CORSConfiguration={"CORSRules": [{"AllowedOrigins": ["*"], "AllowedMethods": ["PUT", "GET"], "AllowedHeaders": ["*"]}]},
    )


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, "")

    def _dispatch(self) -> None:
        url = urlsplit(self.path)
        for method, template, pattern, module in COMPILED:
            match = pattern.match(url.path)
            if method == self.command and match:
                length = int(self.headers.get("Content-Length") or 0)
                event = {
                    "routeKey": f"{method} {template}",
                    "rawPath": url.path,
                    "queryStringParameters": dict(parse_qsl(url.query)) or None,
                    "pathParameters": match.groupdict() or None,
                    "headers": {k.lower(): v for k, v in self.headers.items()},
                    "body": self.rfile.read(length).decode() if length else None,
                }
                resp = module.lambda_handler(event, None)
                self._send(resp["statusCode"], resp["body"])
                return
        self._send(404, json.dumps({"ok": False, "error": {"code": "NOT_FOUND", "message": url.path}}))

    do_GET = do_POST = do_PUT = _dispatch  # noqa: N815

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[api] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}\n")


def main() -> None:
    moto = ThreadedMotoServer(ip_address="127.0.0.1", port=MOTO_PORT, verbose=False)
    moto.start()
    setup_aws()
    vision._bedrock_client = lambda: FixtureBedrock()  # type: ignore[assignment]
    coach.run_agent = _local_coach  # type: ignore[assignment]
    seeded = seed.run()
    print(f"Seeded demo data: {seeded}", flush=True)
    print(f"Local API ready on http://localhost:{API_PORT}  (mock AWS on :{MOTO_PORT})", flush=True)
    lib_http.logger.setLevel("WARNING")
    try:
        ThreadingHTTPServer(("127.0.0.1", API_PORT), Handler).serve_forever()
    finally:
        moto.stop()


if __name__ == "__main__":
    main()
