"""Data models for the calendar manager."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID, uuid4
import zoneinfo

@dataclass
class Attendee:
    """Represents an attendee of an event."""
    name: str
    email: str
    response_status: str = "needsAction"  # Can be: "needsAction", "declined", "tentative", or "accepted"

    @property
    def first_name(self) -> str:
        """Get the attendee's first name.
        
        Returns:
            First name extracted from the full name
        """
        return self.name.split()[0]

    @property
    def has_declined(self) -> bool:
        """Check if the attendee has declined the event.
        
        Returns:
            bool: True if the attendee has declined
        """
        return self.response_status == "declined"

@dataclass
class Person:
    """Represents a person in the calendar system."""
    name: str
    email: str
    title: str
    level: str
    start_date: str
    tenure: str
    metro: str
    location: str
    manager: str
    role: Optional[str] = None

    # Metro code to default timezone mapping (used for non-US/Canada locations)
    METRO_TIMEZONES = {
        'USD - SF/NY': 'America/New_York',  # Default for NY
        'USD - USA': 'America/Chicago',     # Default for USA
        'CAD - Canada': 'America/Toronto',  # Default for Canada
        'GBP - UK': 'Europe/London',
        'SGD - Singapore': 'Asia/Singapore',
        'INR - India': 'Asia/Kolkata',
    }

    # US state to timezone mapping
    US_STATE_TIMEZONES = {
        'AK': 'America/Anchorage',
        'AL': 'America/Chicago',
        'AR': 'America/Chicago',
        'AZ': 'America/Phoenix',
        'CA': 'America/Los_Angeles',
        'CO': 'America/Denver',
        'CT': 'America/New_York',
        'DC': 'America/New_York',
        'DE': 'America/New_York',
        'FL': 'America/New_York',
        'GA': 'America/New_York',
        'HI': 'Pacific/Honolulu',
        'IA': 'America/Chicago',
        'ID': 'America/Boise',
        'IL': 'America/Chicago',
        'IN': 'America/Indiana/Indianapolis',
        'KS': 'America/Chicago',
        'KY': 'America/New_York',
        'LA': 'America/Chicago',
        'MA': 'America/New_York',
        'MD': 'America/New_York',
        'ME': 'America/New_York',
        'MI': 'America/Detroit',
        'MN': 'America/Chicago',
        'MO': 'America/Chicago',
        'MS': 'America/Chicago',
        'MT': 'America/Denver',
        'NC': 'America/New_York',
        'ND': 'America/Chicago',
        'NE': 'America/Chicago',
        'NH': 'America/New_York',
        'NJ': 'America/New_York',
        'NM': 'America/Denver',
        'NV': 'America/Los_Angeles',
        'NY': 'America/New_York',
        'OH': 'America/New_York',
        'OK': 'America/Chicago',
        'OR': 'America/Los_Angeles',
        'PA': 'America/New_York',
        'RI': 'America/New_York',
        'SC': 'America/New_York',
        'SD': 'America/Chicago',
        'TN': 'America/Chicago',
        'TX': 'America/Chicago',
        'UT': 'America/Denver',
        'VA': 'America/New_York',
        'VT': 'America/New_York',
        'WA': 'America/Los_Angeles',
        'WI': 'America/Chicago',
        'WV': 'America/New_York',
        'WY': 'America/Denver',
    }

    # Canadian province to timezone mapping
    CANADA_PROVINCE_TIMEZONES = {
        'AB': 'America/Edmonton',    # Alberta
        'BC': 'America/Vancouver',   # British Columbia
        'MB': 'America/Winnipeg',    # Manitoba
        'NB': 'America/Halifax',     # New Brunswick
        'NL': 'America/St_Johns',    # Newfoundland and Labrador
        'NS': 'America/Halifax',     # Nova Scotia
        'NT': 'America/Yellowknife', # Northwest Territories
        'NU': 'America/Iqaluit',     # Nunavut
        'ON': 'America/Toronto',     # Ontario
        'PE': 'America/Halifax',     # Prince Edward Island
        'QC': 'America/Montreal',    # Quebec
        'SK': 'America/Regina',      # Saskatchewan
        'YT': 'America/Whitehorse',  # Yukon
    }

    @property
    def first_name(self) -> str:
        """Get the person's first name.
        
        Returns:
            First name extracted from the full name
        """
        return self.name.split()[0]

    def get_timezone(self) -> zoneinfo.ZoneInfo:
        """Get the person's timezone based on their location.
        
        For US and Canadian locations, uses state/province information.
        For other locations, uses metro-based mapping.
        
        Returns:
            ZoneInfo object representing the person's timezone
            
        Raises:
            ValueError: If no timezone mapping exists for the location
        """
        # Parse location string (format: "City, State, Country")
        try:
            _, state_code, country = [part.strip() for part in self.location.split(',')]
        except ValueError:
            # If location format doesn't match, fall back to metro-based timezone
            if self.metro not in self.METRO_TIMEZONES:
                raise ValueError(f"No timezone mapping found for metro: {self.metro}")
            return zoneinfo.ZoneInfo(self.METRO_TIMEZONES[self.metro])

        # For US locations
        if country == 'US':
            if state_code not in self.US_STATE_TIMEZONES:
                raise ValueError(f"No timezone mapping found for US state: {state_code}")
            return zoneinfo.ZoneInfo(self.US_STATE_TIMEZONES[state_code])

        # For Canadian locations
        if country == 'CA':
            if state_code not in self.CANADA_PROVINCE_TIMEZONES:
                raise ValueError(f"No timezone mapping found for Canadian province: {state_code}")
            return zoneinfo.ZoneInfo(self.CANADA_PROVINCE_TIMEZONES[state_code])

        # For other countries, use metro-based mapping
        if self.metro not in self.METRO_TIMEZONES:
            raise ValueError(f"No timezone mapping found for metro: {self.metro}")
        return zoneinfo.ZoneInfo(self.METRO_TIMEZONES[self.metro])

@dataclass
class Event:
    """Represents a calendar event."""
    title: str
    id: str
    start_time: datetime
    end_time: datetime
    attendees: List[Attendee] = field(default_factory=list)
    organizer: Optional[Person] = None