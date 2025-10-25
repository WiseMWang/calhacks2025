import os
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive.readonly',
]

# Token storage path (adjust if needed)
TOKEN_PATH = Path(__file__).parent.parent.parent / 'token.json'
CREDENTIALS_PATH = Path(__file__).parent.parent.parent / 'credentials.json'


def get_google_credentials() -> Credentials:
    """Get Google OAuth credentials"""
    creds = None

    # Load existing token
    if TOKEN_PATH.exists():
        logger.info("Loading existing credentials")
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing credentials")
            creds.refresh(Request())
        else:
            logger.info("Starting OAuth flow")
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return creds