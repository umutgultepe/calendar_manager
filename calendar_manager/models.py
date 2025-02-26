"""Data models for the calendar manager."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID, uuid4

@dataclass
class Attendee:
    """Represents an attendee of an event."""
    name: str
    email: str

    @property
    def first_name(self) -> str:
        """Get the attendee's first name.
        
        Returns:
            First name extracted from the full name
        """
        return self.name.split()[0]

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

    @property
    def first_name(self) -> str:
        """Get the person's first name.
        
        Returns:
            First name extracted from the full name
        """
        return self.name.split()[0]

@dataclass
class Event:
    """Represents a calendar event."""
    title: str
    id: str
    start_time: datetime
    end_time: datetime
    attendees: List[Attendee] = field(default_factory=list)
    organizer: Optional[Person] = None