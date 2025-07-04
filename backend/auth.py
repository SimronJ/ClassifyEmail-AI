from fastapi import APIRouter, Request, Response, status
from fastapi.responses import RedirectResponse, JSONResponse
import os
from urllib.parse import urlencode
import httpx

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPE = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify openid email profile"
FRONTEND_URL = "http://localhost:3000/"

@router.get("/login")
def login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url)

@router.get("/callback")
def callback(code: str):
    # Exchange code for tokens
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    try:
        response = httpx.post(GOOGLE_TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        response.raise_for_status()
        tokens = response.json()
        # Redirect to frontend with access_token in query param
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        if access_token and refresh_token:
            redirect_url = f"{FRONTEND_URL}?access_token={access_token}&refresh_token={refresh_token}"
            return RedirectResponse(redirect_url)
        elif access_token:
            redirect_url = f"{FRONTEND_URL}?access_token={access_token}"
            return RedirectResponse(redirect_url)
        else:
            return JSONResponse({"error": "No access token received."}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400) 