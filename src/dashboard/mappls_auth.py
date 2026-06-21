"""Mappls OAuth token helper (optional fallback if Map SDK key expires)."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from src.config import MAPPLS_CLIENT_ID, MAPPLS_CLIENT_SECRET

TOKEN_URL = "https://outpost.mappls.com/api/security/oauth/token"


def fetch_oauth_token() -> str:
    if not MAPPLS_CLIENT_ID or not MAPPLS_CLIENT_SECRET:
        raise ValueError("MAPPLS_CLIENT_ID and MAPPLS_CLIENT_SECRET required in .env")

    data = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": MAPPLS_CLIENT_ID,
            "client_secret": MAPPLS_CLIENT_SECRET,
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "EventOps/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read().decode())
    return str(body["access_token"])
