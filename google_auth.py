import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config

# Define the scopes needed for Gmail, Calendar, and Drive
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/drive'
]

def get_google_credentials():
    """Gets valid user credentials from disk or initiates the OAuth flow."""
    creds = None
    
    # If GOOGLE_TOKEN_JSON environment variable is set (useful for cloud deployments like Railway),
    # write it to the local token.json file first.
    env_token_json = os.getenv('GOOGLE_TOKEN_JSON')
    if env_token_json:
        try:
            with open(config.TOKEN_FILE, 'w') as token_file:
                token_file.write(env_token_json)
            print("Successfully loaded Google token credentials from GOOGLE_TOKEN_JSON environment variable.")
        except Exception as e:
            print(f"Warning: Failed to write token.json from environment variable: {e}")

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(config.TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Warning: Failed to load existing token.json: {e}")
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Warning: Failed to refresh credentials: {e}")
                creds = None

        if not creds:
            if not os.path.exists(config.CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"CRITICAL: Google credentials file '{config.CREDENTIALS_FILE}' is missing!\n"
                    "Please download 'credentials.json' (Desktop App type) from Google Cloud Console "
                    "and place it in the project directory."
                )
            
            # Run the authorization flow
            flow = InstalledAppFlow.from_client_secrets_file(config.CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(config.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

    return creds

def get_google_service(service_name, version):
    """Builds and returns a Google API service instance."""
    creds = get_google_credentials()
    return build(service_name, version, credentials=creds)
