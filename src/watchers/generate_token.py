# generate_token.py
# Run this script ONCE to generate token.json from gmail_credentials.json.
# Place this file in the same folder as gmail_credentials.json (src/watchers/).
#
#   python generate_token.py
#
# It opens a browser for Google consent, then writes token.json next to this
# script — the same path gmail_watcher.py reads from.

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the existing token.json first.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Resolve paths relative to this file so the script works from any cwd.
HERE = Path(__file__).resolve().parent
CREDENTIALS_PATH = HERE / 'gmail_credentials.json'
TOKEN_PATH = HERE / 'token.json'


def main():
    creds = None

    # Reuse an existing token if present, refreshing it if it has expired.
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Existing token expired — refreshing...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"gmail_credentials.json not found at {CREDENTIALS_PATH}. "
                    "Download an OAuth 'Desktop app' client from Google Cloud Console "
                    "and save it there (see SETUP.md)."
                )
            print("No valid token — launching browser for Google consent...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Persist the (new or refreshed) credentials.
        TOKEN_PATH.write_text(creds.to_json())

    print("Token generated successfully!")
    print(f"token.json has been created at: {TOKEN_PATH}")
    print("You can now run gmail_watcher.py.")

    # Quick sanity check that the token actually works.
    try:
        from googleapiclient.discovery import build

        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"Verified access for: {profile.get('emailAddress', 'unknown')}")
    except Exception as e:
        print(f"Test connection failed: {e}")


if __name__ == '__main__':
    main()
