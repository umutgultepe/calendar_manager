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
    id: UUID = field(default_factory=uuid4)
    phone: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

@dataclass
class Event:
    """Represents a calendar event."""
    title: str
    start_time: datetime
    id: UUID = field(default_factory=uuid4)
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: List[Person] = field(default_factory=list)
    organizer: Optional[Person] = None
    is_all_day: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and set default values after initialization."""
        if self.end_time is None and not self.is_all_day:
            # Default duration of 1 hour if not specified and not an all-day event
            self.end_time = self.start_time.replace(hour=self.start_time.hour + 1)
        
        # Ensure end_time is after start_time
        if self.end_time and self.end_time < self.start_time:
            raise ValueError("End time must be after start time") 