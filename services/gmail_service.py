import base64
import html
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from typing import Any
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv

from storage.store import get_connected_account, save_connected_account


load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback"
)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GMAIL_MESSAGES_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def is_google_oauth_configured() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI)


def is_gmail_connected() -> bool:
    return get_connected_account("google") is not None


def gmail_connection_status() -> dict[str, Any]:
    account = get_connected_account("google")
    scopes = account.get("scopes", []) if account else []
    return {
        "configured": is_google_oauth_configured(),
        "connected": account is not None,
        "provider": "google",
        "integration": "gmail",
        "email": account.get("provider_email") if account else None,
        "hasGmailReadonlyScope": "https://www.googleapis.com/auth/gmail.readonly" in scopes,
        "scopes": scopes,
    }


def build_google_auth_url(state: str = "oh-my-kingdom") -> str:
    if not is_google_oauth_configured():
        raise RuntimeError("Google OAuth is not configured.")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_google_code(code: str) -> dict[str, Any]:
    if not is_google_oauth_configured():
        raise RuntimeError("Google OAuth is not configured.")

    token_response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    token_response.raise_for_status()
    token_data = token_response.json()

    user_response = httpx.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        timeout=15,
    )
    user_response.raise_for_status()
    user_info = user_response.json()

    expires_in = int(token_data.get("expires_in", 3600))
    account = {
        "provider_email": user_info.get("email"),
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "scopes": token_data.get("scope", " ".join(GOOGLE_SCOPES)).split(),
        "token_expires_at": (
            datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        ).isoformat(),
    }
    save_connected_account("google", account)
    return {
        "provider": "google",
        "email": account["provider_email"],
        "scopes": account["scopes"],
    }


def _refresh_access_token(account: dict) -> dict:
    refresh_token = account.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Google refresh token is missing. Reconnect Gmail.")

    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    response.raise_for_status()
    token_data = response.json()
    expires_in = int(token_data.get("expires_in", 3600))
    updated = {
        **account,
        "access_token": token_data["access_token"],
        "token_expires_at": (
            datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        ).isoformat(),
    }
    save_connected_account("google", updated)
    return updated


def _get_valid_account() -> dict:
    account = get_connected_account("google")
    if not account:
        raise RuntimeError("Gmail is not connected.")

    expires_at = account.get("token_expires_at")
    if expires_at:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if parsed <= datetime.now(timezone.utc) + timedelta(minutes=2):
            return _refresh_access_token(account)

    return account


def _gmail_get(url: str, account: dict, params: dict | None = None) -> dict:
    response = httpx.get(
        url,
        params=params,
        headers={"Authorization": f"Bearer {account['access_token']}"},
        timeout=15,
    )
    if response.status_code == 401:
        account = _refresh_access_token(account)
        response = httpx.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {account['access_token']}"},
            timeout=15,
        )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise RuntimeError(f"Gmail API returned {exc.response.status_code}: {detail}") from exc
    return response.json()


def _decode_base64url(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode()).decode("utf-8", errors="replace")


def _headers(payload: dict) -> dict[str, str]:
    return {
        header["name"].lower(): header["value"]
        for header in payload.get("headers", [])
        if "name" in header and "value" in header
    }


def _extract_body(payload: dict) -> str:
    body_data = payload.get("body", {}).get("data")
    if body_data:
        return _decode_base64url(body_data)

    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return _decode_base64url(part["body"]["data"])

    for part in payload.get("parts", []):
        nested = _extract_body(part)
        if nested:
            return nested

    return ""


def _clean_body(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def read_latest_email() -> dict[str, str]:
    account = _get_valid_account()
    messages = _gmail_get(
        GMAIL_MESSAGES_URL,
        account,
        params={"maxResults": 1, "labelIds": "INBOX", "q": "newer_than:30d"},
    )
    items = messages.get("messages", [])
    if not items:
        raise RuntimeError("No Gmail messages found in the inbox.")

    message_id = items[0]["id"]
    message = _gmail_get(
        f"{GMAIL_MESSAGES_URL}/{message_id}",
        account,
        params={"format": "full"},
    )
    payload = message.get("payload", {})
    headers = _headers(payload)
    sender_name, sender_email = parseaddr(headers.get("from", ""))
    body = _clean_body(_extract_body(payload) or message.get("snippet", ""))

    return {
        "id": message_id,
        "subject": headers.get("subject", "(no subject)"),
        "sender": sender_email or sender_name or headers.get("from", ""),
        "body": body or message.get("snippet", ""),
    }
