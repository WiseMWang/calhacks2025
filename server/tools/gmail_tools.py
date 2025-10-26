from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText
import os
import logging
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
logger = logging.getLogger(__name__)

class GmailTools:
    def __init__(self, credentials_path=None):
        creds_path = credentials_path or os.path.join(os.path.dirname(__file__), "../../credentials/credentials.json")
        token_path = os.path.join(os.path.dirname(__file__), "../../token.json")
        self.service = self._build_service(creds_path, token_path)

    def _build_service(self, creds_path: str, token_path: str):
        """Authenticate with Gmail and return a Gmail API service."""
        creds = None

        # Load previously saved access/refresh tokens
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # If there are no (valid) credentials, do OAuth login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save new credentials for next time
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        logger.info("✅ Gmail credentials loaded successfully")
        return build("gmail", "v1", credentials=creds)
    
    def send_email(self, to, subject, body, cc=None):
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = ', '.join(cc)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return self.service.users().messages().send(
            userId='me', body={'raw': raw_message}
        ).execute()
    
    def list_messages(self, query="", max_results=10):
        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()
        return results.get('messages', [])
    
    def get_message(self, message_id):
        return self.service.users().messages().get(
            userId='me', id=message_id
        ).execute()

