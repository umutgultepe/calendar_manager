"""Manager for handling one-on-one meetings."""

import os
import json
from pathlib import Path
import yaml
from datetime import datetime, timedelta, time
from typing import List, Optional, Dict
import zoneinfo

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
        self._load_meeting_frequency()

    def _load_meeting_frequency(self) -> None:
        """Load meeting frequency configuration from YAML file."""
        config_path = 'calendar_manager/config/meeting_frequency.yaml'
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Meeting frequency config not found: {config_path}")
            
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def _get_meeting_frequency_weeks(self, person: Person) -> int:
        """Get the meeting frequency in weeks for a person based on their role and title.
        
        Args:
            person: Person to get meeting frequency for
            
        Returns:
            Number of weeks between meetings
            
        Raises:
            ValueError: If no matching frequency is found for the person's role or title
        """
        # First check role-based frequency
        if person.role and 'roles' in self.config and person.role in self.config['roles']:
            return self.config['roles'][person.role]
            
        # Fall back to title-based frequency
        if 'titles' in self.config and person.title in self.config['titles']:
            return self.config['titles'][person.title]
            
        # No matching frequency found
        raise ValueError(
            f"No meeting frequency found for person: {person.name} "
            f"(role: {person.role or 'None'}, title: {person.title})"
        )

    def get_next_recommended_date(self, username: str, days_back: int = 30) -> Optional[datetime]:
        """Get the recommended date for the next 1:1 meeting with a person.
        
        Args:
            username: Username (without @abnormalsecurity.com)
            days_back: Number of days to look back for last meeting (default: 30)
            
        Returns:
            Recommended date for next meeting, or None if person not found
        """
        # Get the person's information
        email = f"{username}@abnormalsecurity.com"
        person = self.person_manager.by_email(email)
        
        if not person:
            return None

        # Get their last meeting
        last_meeting = self.get_last_by_username(username, days_back=days_back)
        
        # Get the frequency in weeks
        frequency_weeks = self._get_meeting_frequency_weeks(person)
        
        # Calculate next date
        if last_meeting:
            # Use the last meeting's date
            base_date = last_meeting.start_time
        else:
            # No previous meeting found, use current date
            base_date = datetime.utcnow()
        
        return base_date + timedelta(weeks=frequency_weeks)

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

    def _is_person_eligible(self, person: Person) -> bool:
        """Check if a person is eligible for 1:1 meetings.
        
        A person is ineligible if:
        - They haven't started yet (start date in the future)
        - The organizer is their manager
        - Their email is in the ignore list
        
        Args:
            person: Person to check
            
        Returns:
            bool: True if person is eligible for 1:1s
        """
        # Check if they haven't started yet
        try:
            start_date = datetime.strptime(person.start_date, '%b %d %Y')
            if start_date > datetime.now():
                return False
        except ValueError:
            # If we can't parse the date, assume they've started
            pass

        # Check if organizer is their manager
        if person.manager == self.organizer.name:
            return False

        # Check if they're in the ignore list
        if 'ignore' in self.config and person.email in self.config['ignore']:
            return False

        return True

    def refresh_next_meetings(self, days_back: int = 30) -> Dict[str, datetime]:
        """Get the next recommended meeting dates for all eligible people.
        
        Args:
            days_back: Number of days to look back for last meetings
            
        Returns:
            Dict mapping email addresses to next meeting dates
        """
        next_meetings = {}
        data_dir = Path('calendar_manager/data')
        data_dir.mkdir(exist_ok=True)
        
        # Get all people
        for email, person in self.person_manager._people_by_email.items():
            if not self._is_person_eligible(person):
                continue
                
            try:
                # Get username from email
                username = email.split('@')[0]
                next_date = self.get_next_recommended_date(username, days_back=days_back)
                
                if next_date:
                    next_meetings[email] = next_date.isoformat()
            except ValueError:
                # Skip people with no matching frequency
                continue

        # Save to file
        with open(data_dir / 'next_meetings.json', 'w') as f:
            json.dump(next_meetings, f, indent=2)

        return next_meetings

    def get_free_slots(self) -> List[datetime]:
        """Get available time slots for meetings in the next business week.
        
        This method:
        1. Finds marked time blocks in the slot calendar
        2. Checks each 30-min slot within those blocks for conflicts
        3. Returns a list of available start times
        
        A time slot is considered conflicting only if there is a meeting with multiple attendees.
        Single-attendee events (like focus time or personal blocks) are not counted as conflicts.
        
        Returns:
            List of datetime objects representing available meeting start times
        """
        # Get slot configuration
        slot_calendar = self.config['organizer']['slot_calendar_name']
        slot_title = self.config['organizer']['slot_title']
        
        # Calculate next business week
        now = datetime.now() + timedelta(days=7)
        start_of_week = now + timedelta(days=(7 - now.weekday()))  # Next Monday
        end_of_week = start_of_week + timedelta(days=5)  # Friday
        
        print(f"\nSearching for '{slot_title}' blocks between:")
        print(f"  Start: {start_of_week.strftime('%A, %B %d, %Y')}")
        print(f"  End:   {end_of_week.strftime('%A, %B %d, %Y')}")
        print(f"  Calendar: {slot_calendar}")
        
        # Get marked time blocks
        time_blocks = self.calendar_client.search_events(
            query=slot_title,
            start_time=start_of_week,
            end_time=end_of_week,
            calendar_id=slot_calendar
        )
        
        if not time_blocks:
            print("\nNo time blocks found with the specified title.")
            return []
            
        print(f"\nFound {len(time_blocks)} time blocks:")
        for block in time_blocks:
            print(f"  • {block.title}: {block.start_time.strftime('%A %I:%M %p')} - {block.end_time.strftime('%I:%M %p')}")
        
        free_slots = []
        total_checked = 0
        total_conflicts = 0
        total_single_attendee = 0
        
        # For each time block
        for block in time_blocks:
            current_time = block.start_time
            
            # Iterate in 30-minute increments
            while current_time < block.end_time:
                slot_end = current_time + timedelta(minutes=30)
                total_checked += 1
                
                # Check for conflicts in primary calendar
                events = self.calendar_client.search_events(
                    query="",  # Empty query to get all events
                    start_time=current_time,
                    end_time=slot_end
                )
                
                # Filter out single-attendee events
                conflicts = [
                    event for event in events
                    if len(event.attendees) > 1  # More than one attendee
                ]
                
                # If no multi-attendee conflicts, add to free slots
                if not conflicts:
                    free_slots.append(current_time)
                    if events:
                        total_single_attendee += 1
                else:
                    total_conflicts += 1
                
                current_time = slot_end
        
        if not free_slots:
            print(f"\nChecked {total_checked} slots:")
            print(f"  • {total_conflicts} had multi-attendee conflicts")
            print(f"  • {total_single_attendee} had only single-attendee events")
            print(f"  • {total_checked - total_conflicts - total_single_attendee} were completely free")
            
        return sorted(free_slots)

    def is_person_free(self, meeting_time: datetime, person_email: str) -> bool:
        """Check if a person is free for a 30-minute meeting at the specified time.
        
        A person is considered free if:
        1. The meeting is during their business hours (9 AM to 5 PM local time)
        2. They don't have any conflicting meetings
        
        Args:
            meeting_time: Timezone-aware datetime for the proposed meeting
            person_email: Email address of the person to check
            
        Returns:
            bool: True if the person is free, False otherwise
            
        Raises:
            ValueError: If person not found or timezone mapping not available
        """
        # Get the person
        person = self.person_manager.by_email(person_email)
        if not person:
            raise ValueError(f"Person not found with email: {person_email}")
            
        # Get their timezone
        tz = person.get_timezone()
        
        # Convert meeting time to person's timezone
        local_time = meeting_time.astimezone(tz)
        
        # Check if it's during business hours (9 AM to 5 PM)
        business_start = time(9, 0)  # 9 AM
        business_end = time(17, 0)   # 5 PM
        
        meeting_end_time = (local_time + timedelta(minutes=30)).time()
        if not (business_start <= local_time.time() and meeting_end_time <= business_end):
            return False
        # Check for conflicts in the 30-minute slot
        meeting_end = meeting_time + timedelta(minutes=30)
        events = self.calendar_client.search_events(
            query="",  # Empty query to get all events
            start_time=meeting_time,
            end_time=meeting_end,
            calendar_id=person_email  # Search in person's calendar
        )
        
        # Filter out single-attendee events
        conflicts = [
            event for event in events
            if len(event.attendees) > 1  # More than one attendee
        ]
        
        return len(conflicts) == 0 