from fastapi import APIRouter, Query
from typing import List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import base64
import re
import os

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

router = APIRouter()

@router.get("/list")
def list_emails(
    access_token: str = Query(..., description="Google OAuth access token"),
    refresh_token: str = Query(..., description="Google OAuth refresh token")
):
    # Check for required environment variables
    if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET]):
        return {"error": "Google client credentials are not set in environment variables."}
    try:
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=GOOGLE_TOKEN_URI,
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=SCOPES,
        )
        service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
        # List messages
        messages_response = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = messages_response.get('messages', [])
        emails = []
        for msg in messages:
            msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full', metadataHeaders=['subject', 'from']).execute()
            subject = ""
            sender = ""
            for header in msg_detail.get('payload', {}).get('headers', []):
                if header['name'].lower() == 'subject':
                    subject = header['value']
                if header['name'].lower() == 'from':
                    sender = header['value']
            # Try to get the full body text
            def get_body(payload):
                if 'body' in payload and payload['body'].get('data'):
                    data = payload['body']['data']
                    try:
                        decoded = base64.urlsafe_b64decode(data + '===').decode('utf-8', errors='replace')
                        return decoded
                    except Exception:
                        try:
                            decoded = base64.urlsafe_b64decode(data + '===').decode('latin1', errors='replace')
                            return decoded
                        except Exception:
                            return ''
                if 'parts' in payload:
                    for part in payload['parts']:
                        body = get_body(part)
                        if body:
                            return body
                return ''
            full_body = get_body(msg_detail.get('payload', {}))
            # Remove HTML tags
            def strip_html(text):
                return re.sub(r'<[^>]+>', '', text)
            plain_body = strip_html(full_body.strip()) if full_body.strip() else ''
            # Keep only a-z, A-Z, 0-9, common English grammar symbols, and whitespace
            def keep_english_text(text):
                return re.sub(r"[^a-zA-Z0-9.,!?;:'\"\-()\[\]{}@#$%&*/+=_~`|<>\\n\\r\\t ]", '', text)
            clean_body = keep_english_text(plain_body)
            snippet = clean_body if clean_body else msg_detail.get('snippet', '')
            emails.append({
                'id': msg['id'],
                'subject': subject,
                'snippet': snippet,
                'sender': sender,
            })
        return {"emails": emails}
    except HttpError as e:
        return {"error": str(e)} 