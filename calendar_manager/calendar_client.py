"""Google Calendar client implementation."""

import os
import pickle
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Event, Attendee

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

        try:
            # Try to get a single calendar entry to validate access
            self.service.calendarList().list(maxResults=1).execute()
            return True
        except HttpError:
            return False
        except Exception:
            return False

    def search_events(self, query: str, start_time: datetime, end_time: datetime, calendar_id: str = 'primary') -> List[Event]:
        """Search for events in the calendar.
        
        Args:
            query: Search query string
            start_time: Start of the search range
            end_time: End of the search range
            calendar_id: ID of the calendar to search (default: 'primary')
            
        Returns:
            List of matching Event objects
        """
        if not self.service:
            self.authenticate()

        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=self._sanitize_date_for_api(start_time),
                timeMax=self._sanitize_date_for_api(end_time),
                singleEvents=True,
                orderBy='startTime',
                q=query
            ).execute()

            events = []
            for item in events_result.get('items', []):
                # Extract attendees
                attendees = []
                for attendee in item.get('attendees', []):
                    attendees.append(Attendee(
                        name=attendee.get('displayName', ''),
                        email=attendee['email'],
                        response_status=attendee.get('responseStatus', 'needsAction')
                    ))

                # Extract start and end times
                start = item['start'].get('dateTime', item['start'].get('date'))
                end = item['end'].get('dateTime', item['end'].get('date'))
                
                # Convert string times to datetime objects
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))

                # Create organizer
                organizer = None
                if 'organizer' in item:
                    organizer = Attendee(
                        name=item['organizer'].get('displayName', ''),
                        email=item['organizer']['email']
                    )

                event = Event(
                    id=item['id'],
                    title=item['summary'],
                    start_time=start_time,
                    end_time=end_time,
                    attendees=attendees,
                    organizer=organizer
                )
                events.append(event)

            return events

        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def _sanitize_date_for_api(self, dt: str | datetime) -> str:
        """
        Sanitize datetime for Google Calendar API.
        If input is string, assumes it's already in ISO format.
        If datetime is timezone-aware, converts to UTC first.
        Ensures output is in ISO format with 'Z' suffix.
        
        Args:
            dt: Datetime object or string to sanitize
            
        Returns:
            ISO format string in UTC with 'Z' suffix
        """
        if isinstance(dt, str):
            return dt if dt.endswith('Z') else dt + 'Z'

        # Convert to UTC first if timezone-aware
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        
        # Format with microseconds only if they exist
        if dt.microsecond:
            formatted = dt.strftime('%Y-%m-%dT%H:%M:%S.%f').rstrip('0')
        else:
            formatted = dt.strftime('%Y-%m-%dT%H:%M:%S')
            
        return formatted + 'Z'

    def schedule_meeting(self, attendee_emails: List[str], start_time: datetime, end_time: datetime, 
                      title: str, calendar_id: str = 'primary') -> Event:
        """Schedule a new meeting in the calendar.
        
        Args:
            attendee_emails: List of attendee email addresses
            start_time: Start time (timezone-aware)
            end_time: End time (timezone-aware)
            title: Meeting title
            calendar_id: ID of the calendar to create event in (default: 'primary')
            
        Returns:
            Event object representing the created meeting
            
        Raises:
            HttpError: If the API request fails
        """
        if not self.service:
            self.authenticate()

        # Create event body
        event_body = {
            'summary': title,
            'start': {
                'dateTime': self._sanitize_date_for_api(start_time),
            },
            'end': {
                'dateTime': self._sanitize_date_for_api(end_time),
            },
            'attendees': [{'email': email} for email in attendee_emails]
        }

        try:
            # Create the event
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_body,
                sendUpdates='all'  # Send email notifications to attendees
            ).execute()

            # Convert to our Event model
            attendees = [
                Attendee(
                    name=attendee.get('displayName', ''),
                    email=attendee['email'],
                    response_status=attendee.get('responseStatus', 'needsAction')
                )
                for attendee in created_event.get('attendees', [])
            ]

            # Create organizer
            organizer = None
            if 'organizer' in created_event:
                organizer = Attendee(
                    name=created_event['organizer'].get('displayName', ''),
                    email=created_event['organizer']['email']
                )

            # Convert times
            start = created_event['start'].get('dateTime', created_event['start'].get('date'))
            end = created_event['end'].get('dateTime', created_event['end'].get('date'))
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))

            return Event(
                id=created_event['id'],
                title=created_event['summary'],
                start_time=start_time,
                end_time=end_time,
                attendees=attendees,
                organizer=organizer
            )

        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
