#!/usr/bin/env python3
"""
Quick script to create token.json for Gmail OAuth
Run this once to authenticate and create the token file.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
]

def create_token():
    creds = None
    token_path = "token.json"
    creds_path = "credentials.json"
    
    # Check if token already exists
    if os.path.exists(token_path):
        print("token.json already exists!")
        return
    
    # Run OAuth flow
    print("Starting OAuth flow...")
    print("A browser window will open. Please sign in and authorize the app.")
    
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the credentials
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    print(f"✅ token.json created successfully!")
    print("Your app will now be fast on subsequent runs.")

if __name__ == "__main__":
    create_token()