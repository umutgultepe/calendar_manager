"""Manager for handling person-related operations."""

import csv
import yaml
from typing import Dict, Optional
from pathlib import Path

from .models import Person

class PersonManager:
    """Manages person-related operations and lookups."""

    def __init__(self, organization_file_path: str, roles_file_path: str = 'calendar_manager/config/roles.yaml'):
        """Initialize the PersonManager.
        
        Args:
            organization_file_path: Path to the organization CSV file
            roles_file_path: Path to the roles YAML file (default: calendar_manager/config/roles.yaml)
        """
        self.organization_file_path = Path(organization_file_path)
        self.roles_file_path = Path(roles_file_path)
        self._people_by_email: Dict[str, Person] = {}
        self._roles_by_email: Dict[str, str] = {}
        self._load_roles_data()
        self._load_organization_data()

    def _load_roles_data(self) -> None:
        """Load roles data from YAML file."""
        if self.roles_file_path.exists():
            with open(self.roles_file_path, 'r') as f:
                roles_data = yaml.safe_load(f)
                if roles_data and 'roles' in roles_data:
                    self._roles_by_email = roles_data['roles']

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
                    manager=row['Manager'],
                    role=self._roles_by_email.get(row['Email'])
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
        """Reload the organization and roles data."""
        self._people_by_email.clear()
        self._roles_by_email.clear()
        self._load_roles_data()
        self._load_organization_data() 