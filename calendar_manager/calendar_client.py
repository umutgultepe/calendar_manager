"""Google Calendar client implementation."""

import os
import pickle
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleCalendarClient:
    """Client for interacting with Google Calendar API."""
    
    # If modifying these scopes, delete the token.pickle file.
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
              'https://www.googleapis.com/auth/calendar.events']
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """Initialize the calendar client.
        
        Args:
            credentials_path: Path to the credentials.json file from Google Cloud Console
        """
        self.credentials_path = credentials_path
        self.creds = None
        self.service = None
        
    def authenticate(self) -> None:
        """Authenticate with Google Calendar API."""
        # Check if we have valid credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('calendar', 'v3', credentials=self.creds)

    def validate_access(self) -> bool:
        """Validate access to Google Calendar API.
        
        Returns:
            bool: True if access is valid, False otherwise
        """
        if not self.service:
            try:
                self.authenticate()
            except Exception:
                return False

            # Try to get a single calendar entry to validate access
        self.service.calendarList().list(maxResults=1).execute()
        return True