"""Manager for handling person-related operations."""

import csv
from typing import Dict, Optional
from pathlib import Path

from .models import Person

class PersonManager:
    """Manages person-related operations and lookups."""

    def __init__(self, organization_file_path: str):
        """Initialize the PersonManager.
        
        Args:
            organization_file_path: Path to the organization CSV file
        """
        self.organization_file_path = Path(organization_file_path)
        self._people_by_email: Dict[str, Person] = {}
        self._load_organization_data()

    def _load_organization_data(self) -> None:
        """Load organization data from CSV file."""
        if not self.organization_file_path.exists():
            raise FileNotFoundError(f"Organization file not found: {self.organization_file_path}")

        with open(self.organization_file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                person = Person(
                    name=row['Name'],
                    email=row['Email'],
                    title=row['Title'],
                    level=row['Level'],
                    start_date=row['Start date'],
                    tenure=row['Tenure'],
                    metro=row['Metro'],
                    location=row['Location'],
                    manager=row['Manager']
                )
                self._people_by_email[person.email] = person

    def by_email(self, email: str) -> Optional[Person]:
        """Get a person by their email address.
        
        Args:
            email: The email address to look up
            
        Returns:
            Person object if found, None otherwise
        """
        return self._people_by_email.get(email)

    def refresh(self) -> None:
        """Reload the organization data from the CSV file."""
        self._people_by_email.clear()
        self._load_organization_data() 