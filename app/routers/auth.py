"""
Auth Router
───────────
Handles Google OAuth 2.0 flow for Gmail access.

Flow:
  1. User visits /auth/login  → redirected to Google consent screen
  2. Google redirects back to /auth/callback with ?code=...
  3. We exchange the code for tokens and store them
  4. User is now authenticated — pipeline can fetch their Gmail
"""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from app.config import get_settings
from app.services.gmail_service import save_tokens

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",   # Read emails
    "https://www.googleapis.com/auth/gmail.send",       # Send replies
    "https://www.googleapis.com/auth/gmail.modify",     # Mark as read
]


def _build_flow() -> Flow:
    settings = get_settings()
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id":     settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                "token_uri":     "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


@router.get("/login")
def login():
    """Redirect user to Google OAuth consent screen."""
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",   # Get refresh token so we can run without user present
        prompt="consent",
    )
    return RedirectResponse(auth_url)


@router.get("/callback")
def callback(code: str):
    """
    Google redirects here after user consents.
    Exchange the code for access + refresh tokens.
    """
    settings = get_settings()
    flow = _build_flow()
    flow.fetch_token(code=code)

    creds = flow.credentials
    save_tokens({
        "access_token":  creds.token,
        "refresh_token": creds.refresh_token,
        "client_id":     settings.google_client_id,
        "client_secret": settings.google_client_secret,
    })

    return {"message": "✅ Gmail conectado correctamente. Ya puedes correr el pipeline."}


@router.get("/status")
def status():
    """Check if Gmail is connected."""
    from app.services.gmail_service import load_tokens
    tokens = load_tokens()
    return {"connected": tokens is not None}
