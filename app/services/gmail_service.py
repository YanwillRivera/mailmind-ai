"""
Gmail Service
─────────────
Handles all communication with the Gmail API:
  - OAuth token management
  - Fetching unread emails
  - Sending replies
"""
import base64
import json
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# ── Token storage (in a real app, store in DB per user) ──────────────────────
_token_store: dict = {}   # { "access_token": ..., "refresh_token": ..., ... }

def save_tokens(tokens: dict):
    """Save OAuth tokens (in production: store in DB, encrypted)."""
    global _token_store
    _token_store = tokens

def load_tokens() -> Optional[dict]:
    return _token_store if _token_store else None


# ── Build authenticated Gmail client ─────────────────────────────────────────
def get_gmail_client():
    tokens = load_tokens()
    if not tokens:
        raise ValueError("No Gmail tokens found. User must authenticate first at /auth/login")

    creds = Credentials(
        token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=tokens["client_id"],
        client_secret=tokens["client_secret"],
    )
    return build("gmail", "v1", credentials=creds)


# ── Fetch unread emails ───────────────────────────────────────────────────────
def fetch_unread_emails(max_results: int = 5) -> list[dict]:
    """
    Fetch unread emails from Gmail inbox.
    Returns a list of parsed email dicts.
    """
    service = get_gmail_client()

    # Search for unread emails in inbox
    result = service.users().messages().list(
        userId="me",
        q="is:unread in:inbox",
        maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    emails = []

    for msg_ref in messages:
        try:
            msg = service.users().messages().get(
                userId="me",
                id=msg_ref["id"],
                format="full"
            ).execute()
            parsed = _parse_gmail_message(msg)
            if parsed:
                emails.append(parsed)
        except HttpError as e:
            print(f"Error fetching message {msg_ref['id']}: {e}")
            continue

    return emails


def _parse_gmail_message(msg: dict) -> Optional[dict]:
    """Extract useful fields from a raw Gmail API message."""
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

    # Extract body text
    body = _extract_body(msg["payload"])

    received_timestamp = int(msg["internalDate"]) / 1000  # ms → seconds
    received_at = datetime.fromtimestamp(received_timestamp)

    sender_raw = headers.get("From", "")
    sender_name, sender_email = _parse_sender(sender_raw)

    return {
        "gmail_id":     msg["id"],
        "sender_email": sender_email,
        "sender_name":  sender_name,
        "subject":      headers.get("Subject", "(sin asunto)"),
        "body":         body,
        "body_preview": body[:500],
        "received_at":  received_at,
        "thread_id":    msg["threadId"],
    }


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    if "parts" in payload:
        for part in payload["parts"]:
            text = _extract_body(part)
            if text:
                return text

    return ""


def _parse_sender(sender_raw: str) -> tuple[str, str]:
    """Parse 'Name <email@example.com>' into (name, email)."""
    if "<" in sender_raw:
        name  = sender_raw.split("<")[0].strip().strip('"')
        email = sender_raw.split("<")[1].strip(">").strip()
    else:
        name  = sender_raw
        email = sender_raw
    return name, email


# ── Mark email as read ────────────────────────────────────────────────────────
def mark_as_read(gmail_id: str):
    service = get_gmail_client()
    service.users().messages().modify(
        userId="me",
        id=gmail_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


# ── Send a reply ──────────────────────────────────────────────────────────────
def send_reply(to_email: str, subject: str, body: str, thread_id: str):
    """Send an email reply in the same Gmail thread."""
    service = get_gmail_client()

    mime_msg = MIMEText(body)
    mime_msg["to"]      = to_email
    mime_msg["subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": thread_id}
    ).execute()
