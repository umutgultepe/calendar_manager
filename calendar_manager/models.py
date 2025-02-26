"""Data models for the calendar manager."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID, uuid4

@dataclass
class Person:
    """Represents a person in the calendar system."""
    name: str
    email: str
    id: str

@dataclass
class Event:
    """Represents a calendar event."""
    title: str
    id: str
    start_time: datetime
    end_time: datetime
    attendees: List[Person] = field(default_factory=list)
    organizer: Optional[Person] = None