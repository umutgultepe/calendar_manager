"""Manager for handling one-on-one meetings."""

from datetime import datetime, timedelta
from typing import List, Optional

from .calendar_client import GoogleCalendarClient
from .person_manager import PersonManager
from .models import Event, Person, Attendee

class OneOnOneManager:
    """Manages one-on-one meeting operations."""

    def __init__(self, organizer: Attendee, person_manager: PersonManager, calendar_client: GoogleCalendarClient):
        """Initialize the OneOnOneManager.
        
        Args:
            person_manager: PersonManager instance for looking up people
            calendar_client: GoogleCalendarClient instance for calendar operations
        """
        self.organizer = organizer
        self.person_manager = person_manager
        self.calendar_client = calendar_client

    def _is_one_on_one_with_person(self, event: Event, person: Person) -> bool:
        """Check if an event is a 1:1 meeting with the specified person.
        
        Args:
            event: Event to check
            person: Person to check against
            
        Returns:
            bool: True if the event is a 1:1 with the person
        """
        # Get the other person's name (either organizer or attendee)
        # Check both possible formats of 1:1 title
        possible_titles = [
            f"{person.first_name} / {self.organizer.first_name}",
            f"{self.organizer.first_name} / {person.first_name}"
        ]

        return event.title in possible_titles

    def get_last_by_username(self, username: str, days_back: int = 30) -> Optional[Event]:
        """Get the last 1:1 meeting with a person by their username.
        
        Args:
            username: Username (without @abnormalsecurity.com)
            days_back: Number of days to look back (default: 30)
            
        Returns:
            Event object if found, None otherwise
        """
        email = f"{username}@abnormalsecurity.com"
        person = self.person_manager.by_email(email)
        
        if not person:
            return None

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)

        # Search for events with the person's name
        events = self.calendar_client.search_events(
            query=person.first_name,
            start_time=start_time,
            end_time=end_time
        )

        # Filter for actual 1:1s and sort by start time (most recent first)
        one_on_ones = [
            event for event in events 
            if self._is_one_on_one_with_person(event, person)
        ]
        one_on_ones.sort(key=lambda x: x.start_time, reverse=True)

        return one_on_ones[0] if one_on_ones else None 