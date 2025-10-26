from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText

class GmailTools:
    def __init__(self, credentials_path=None):
        if credentials_path:
            self.service = build('gmail', 'v1', credentials=self.load_creds(credentials_path))
    
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

# Standalone function for backward compatibility
def send_email(to, subject, body, cc=None):
    gmail = GmailTools()
    return gmail.send_email(to, subject, body, cc)
