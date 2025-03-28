"""Command line interface for Calendar Manager."""

import os
import yaml
import click
from datetime import datetime, timedelta
from .calendar_client import GoogleCalendarClient
from .person_manager import PersonManager
from .one_on_one_manager import OneOnOneManager
from .models import Attendee
import zoneinfo
from typing import Optional, Tuple

def _load_config():
    """Load configuration from meeting_frequency.yaml."""
    config_path = 'calendar_manager/config/meeting_frequency.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Meeting frequency config not found: {config_path}")
        
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

@click.group()
def main():
    """Calendar Manager CLI - Manage your calendar from the command line."""
    pass

@main.command()
@click.option('--credentials', '-c', 
              default='credentials.json',
              help='Path to the credentials.json file from Google Cloud Console')
def validate_access(credentials):
    """Validate access to Google Calendar."""
    if not os.path.exists(credentials):
        click.echo(f"Error: Credentials file not found at {credentials}")
        click.echo("Please download credentials.json from Google Cloud Console and try again.")
        return

    click.echo("Initializing Google Calendar client...")
    client = GoogleCalendarClient(credentials_path=credentials)
    
    click.echo("Validating access to Google Calendar...")
    if client.validate_access():
        click.echo("✅ Successfully connected to Google Calendar!")
    else:
        click.echo("❌ Failed to access Google Calendar. Please check your credentials and try again.")

@main.command()
@click.argument('username')
@click.option('--days', '-d', default=30, help='Number of days to look back')
@click.option('--org-file', '-o',
              default='calendar_manager/config/organization.csv',
              help='Path to the organization CSV file')
@click.option('--credentials', '-c',
              default='credentials.json',
              help='Path to the credentials.json file')
def get_last_by_username(username: str, days: int, org_file: str, credentials: str):
    """Find the last 1:1 meeting with a person by their username."""
    try:
        # Initialize dependencies
        person_manager = PersonManager(org_file)
        calendar_client = GoogleCalendarClient(credentials)

        # Get the organizer information
        # Load organizer info from meeting_frequency.yaml
        with open('calendar_manager/config/meeting_frequency.yaml', 'r') as f:
            config = yaml.safe_load(f)
            organizer = Attendee(
                name=config['organizer']['name'],
                email=config['organizer']['email']
            )

        # Initialize the 1:1 manager
        one_on_one_manager = OneOnOneManager(
            organizer=organizer,
            person_manager=person_manager,
            calendar_client=calendar_client
        )

        # Get the last 1:1
        last_meeting = one_on_one_manager.get_last_by_username(username, days_back=days)

        if not last_meeting:
            click.echo(f"❌ No 1:1 meetings found with {username} in the last {days} days.")
            return

        # Format and display the meeting information
        click.echo("\n📅 Last 1:1 Meeting Details:")
        click.echo("─" * 50)
        click.echo(f"Title:     {last_meeting.title}")
        click.echo(f"Date:      {last_meeting.start_time.strftime('%Y-%m-%d')}")
        click.echo(f"Time:      {last_meeting.start_time.strftime('%H:%M')} - {last_meeting.end_time.strftime('%H:%M')}")
        
        # Show attendees
        if last_meeting.attendees:
            click.echo("\nAttendees:")
            for attendee in last_meeting.attendees:
                click.echo(f"  • {attendee.name} ({attendee.email})")
        
        click.echo("─" * 50)

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {str(e)}")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")

@main.command()
@click.argument('email')
@click.option('--org-file', '-o',
              default='calendar_manager/config/organization.csv',
              help='Path to the organization CSV file')
def person(email, org_file):
    """Display information about a person by their email."""
    try:
        # Load config to get domain
        config = _load_config()
        if 'domain' not in config:
            raise ValueError("Domain not found in configuration file")
        domain = config['domain']
        
        manager = PersonManager(org_file)
        person = manager.by_email(email + f'@{domain}')
        
        if not person:
            click.echo(f"❌ No person found with email: {email}@{domain}")
            return
        
        # Get timezone information
        try:
            tz = person.get_timezone()
            current_time = datetime.now(tz)
            tz_name = str(tz)
            tz_offset = current_time.strftime('%z')  # Format: +HHMM or -HHMM
            current_time_str = current_time.strftime('%I:%M %p')
        except ValueError as e:
            tz_info = f"Error: {str(e)}"
            tz_name = "Unknown"
            tz_offset = "N/A"
            current_time_str = "N/A"
        
        # Display person information in a formatted way
        click.echo("\n📋 Person Information:")
        click.echo("─" * 50)
        click.echo(f"Name:      {person.name}")
        click.echo(f"Email:     {person.email}")
        click.echo(f"Title:     {person.title}")
        click.echo(f"Level:     {person.level}")
        click.echo(f"Location:  {person.location} ({person.metro})")
        click.echo(f"Started:   {person.start_date} ({person.tenure})")
        click.echo(f"Manager:   {person.manager}")
        click.echo(f"Role:      {person.role or 'Not assigned'}")
        click.echo("─" * 50)
        click.echo("🌐 Timezone Information:")
        click.echo(f"Timezone:  {tz_name}")
        click.echo(f"Offset:    UTC{tz_offset}")
        click.echo(f"Local:     {current_time_str}")
        click.echo("─" * 50)
        
    except FileNotFoundError:
        click.echo(f"❌ Organization file not found at: {org_file}")
    except Exception as e:
        click.echo(f"❌ Error retrieving person information: {str(e)}")

@main.command()
@click.argument('username')
@click.option('--days', '-d', default=30, help='Number of days to look back')
@click.option('--org-file', '-o',
              default='calendar_manager/config/organization.csv',
              help='Path to the organization CSV file')
@click.option('--credentials', '-c',
              default='credentials.json',
              help='Path to the credentials.json file')
def next_one_on_one(username: str, days: int, org_file: str, credentials: str):
    """Get the recommended date for the next 1:1 meeting with a person."""
    try:
        # Initialize dependencies
        person_manager = PersonManager(org_file)
        calendar_client = GoogleCalendarClient(credentials)

        # Get the organizer information
        with open('calendar_manager/config/meeting_frequency.yaml', 'r') as f:
            config = yaml.safe_load(f)
            organizer = Attendee(
                name=config['organizer']['name'],
                email=config['organizer']['email']
            )

        # Initialize the 1:1 manager
        one_on_one_manager = OneOnOneManager(
            organizer=organizer,
            person_manager=person_manager,
            calendar_client=calendar_client
        )

        # Get the next recommended date
        try:
            next_date = one_on_one_manager.get_next_recommended_date(username, days_back=days)
        except ValueError as e:
            click.echo(f"❌ {str(e)}")
            return

        if not next_date:
            click.echo(f"❌ Could not determine next meeting date for {username}.")
            return

        # Get the person's information for context
        person = person_manager.by_email(f"{username}@abnormalsecurity.com")
        
        # Get the frequency for display
        frequency = one_on_one_manager._get_meeting_frequency_weeks(person)
        frequency_text = {
            1: "Weekly",
            2: "Bi-weekly",
            4: "Monthly"
        }.get(frequency, f"Every {frequency} weeks")
        
        # Format and display the information
        click.echo("\n📅 Next 1:1 Meeting Recommendation:")
        click.echo("─" * 50)
        click.echo(f"Person:     {person.name}")
        if person.role:
            click.echo(f"Role:       {person.role}")
        click.echo(f"Title:      {person.title}")
        click.echo(f"Frequency:  {frequency_text}")
        click.echo(f"Next Date:  {next_date.strftime('%A, %B %d, %Y')}")
        click.echo("─" * 50)

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {str(e)}")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")

@main.command()
@click.option('--days', '-d', default=60, help='Number of days to look back')
@click.option('--org-file', '-o',
              default='calendar_manager/config/organization.csv',
              help='Path to the organization CSV file')
@click.option('--credentials', '-c',
              default='credentials.json',
              help='Path to the credentials.json file')
def refresh_dataset(days: int, org_file: str, credentials: str):
    """Refresh the dataset of next recommended 1:1 meetings."""
    try:
        # Initialize dependencies
        person_manager = PersonManager(org_file)
        calendar_client = GoogleCalendarClient(credentials)

        # Get the organizer information
        with open('calendar_manager/config/meeting_frequency.yaml', 'r') as f:
            config = yaml.safe_load(f)
            organizer = Attendee(
                name=config['organizer']['name'],
                email=config['organizer']['email']
            )

        # Initialize the 1:1 manager
        one_on_one_manager = OneOnOneManager(
            organizer=organizer,
            person_manager=person_manager,
            calendar_client=calendar_client
        )

        # Refresh the dataset
        next_meetings = one_on_one_manager.refresh_next_meetings(days_back=days)
        
        # Display summary
        click.echo("\n📊 Dataset Refresh Summary:")
        click.echo("─" * 50)
        click.echo(f"Total eligible people: {len(next_meetings)}")
        
        # Show next few meetings
        if next_meetings:
            click.echo("\nUpcoming meetings (next 5):")
            # Sort by date
            sorted_meetings = sorted(
                next_meetings.items(), 
                key=lambda x: x[1]
            )[:5]
            
            for email, date_str in sorted_meetings:
                person = person_manager.by_email(email)
                date = datetime.fromisoformat(date_str)
                click.echo(f"  • {person.name:<30} {date.strftime('%A, %B %d, %Y')}")
        
        click.echo("\n✅ Dataset saved to: calendar_manager/data/next_meetings.json")
        click.echo("─" * 50)

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {str(e)}")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")

def _get_default_date_range() -> Tuple[datetime, datetime]:
    """Get default date range for meetings (next business week).
    
    Returns:
        Tuple of (start_date, end_date) where:
        - start_date defaults to next Monday
        - end_date defaults to next Friday
    """
    now = datetime.now()
    # Default to next Monday
    start_date = now + timedelta(days=(7 - now.weekday()))
    # Default to end of next business week (Friday)
    end_date = start_date + timedelta(days=4)
    
    # Ensure dates are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=now.astimezone().tzinfo)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=now.astimezone().tzinfo)
        
    # Set end_date to end of day
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    return start_date, end_date

@main.command()
@click.option('--start-date', '-s', type=str,
              help='Start date in YYYY-MM-DD format (defaults to next Monday)')
@click.option('--end-date', '-e', type=str,
              help='End date in YYYY-MM-DD format (defaults to next Friday)')
@click.option('--org-file', '-o',
              default='calendar_manager/config/organization.csv',
              help='Path to the organization CSV file')
@click.option('--credentials', '-c',
              default='credentials.json',
              help='Path to the credentials.json file')
def free_slots(start_date: Optional[str], end_date: Optional[str], org_file: str, credentials: str):
    """Show available time slots for meetings in the specified date range.
    
    If no dates are provided, shows slots for the next business week.
    """
    try:
        # Initialize dependencies
        person_manager = PersonManager(org_file)
        calendar_client = GoogleCalendarClient(credentials)

        # Get the organizer information
        with open('calendar_manager/config/meeting_frequency.yaml', 'r') as f:
            config = yaml.safe_load(f)
            organizer = Attendee(
                name=config['organizer']['name'],
                email=config['organizer']['email']
            )

        # Initialize the 1:1 manager
        one_on_one_manager = OneOnOneManager(
            organizer=organizer,
            person_manager=person_manager,
            calendar_client=calendar_client
        )

        # Parse dates if provided, otherwise use defaults
        start = None
        end = None
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                click.echo("❌ Invalid start date format. Please use YYYY-MM-DD")
                return
                
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                click.echo("❌ Invalid end date format. Please use YYYY-MM-DD")
                return

        if not start or not end:
            default_start, default_end = _get_default_date_range()
            if not start:
                start = default_start
            if not end:
                end = default_end

        # Get free slots
        slots = one_on_one_manager.get_free_slots(start_date=start, end_date=end)
        
        if not slots:
            click.echo("❌ No available time slots found in the specified date range.")
            return
            
        # Display available slots
        click.echo("\n📅 Available Time Slots:")
        click.echo("─" * 50)
        
        # Group by day
        current_day = None
        for slot in slots:
            day = slot.strftime('%A, %B %d')
            if day != current_day:
                current_day = day
                click.echo(f"\n{day}:")
            
            click.echo(f"  • {slot.strftime('%I:%M %p')}")
        
        click.echo("\n")
        click.echo("─" * 50)
        click.echo(f"Total available slots: {len(slots)}")

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {str(e)}")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")

@main.command()
@click.argument('username')
@click.argument('date')
@click.argument('time')
@click.option('--org-file', '-o',
              default='calendar_manager/config/organization.csv',
              help='Path to the organization CSV file')
@click.option('--credentials', '-c',
              default='credentials.json',
              help='Path to the credentials.json file')
def is_free(username: str, date: str, time: str, org_file: str, credentials: str):
    """Check if a person is free for a 30-minute meeting.
    
    Arguments:
        username: Username (without domain)
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour) in YOUR timezone
    """
    try:
        # Load config
        config = _load_config()
        domain = config.get('domain', 'abnormalsecurity.com')  # Default fallback

        # Initialize dependencies
        person_manager = PersonManager(org_file)
        calendar_client = GoogleCalendarClient(credentials)

        # Get the organizer information
        organizer = Attendee(
            name=config['organizer']['name'],
            email=config['organizer']['email']
        )

        # Initialize the 1:1 manager
        one_on_one_manager = OneOnOneManager(
            organizer=organizer,
            person_manager=person_manager,
            calendar_client=calendar_client
        )

        # Get the person's information
        email = f"{username}@{domain}"
        person = person_manager.by_email(email)
        
        if not person:
            click.echo(f"❌ No person found with email: {email}")
            return

        try:
            # Parse date and time and make it timezone-aware in user's timezone
            user_tz = zoneinfo.ZoneInfo('America/Los_Angeles')  # Default to PT for the organizer
            meeting_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            meeting_datetime = meeting_datetime.replace(tzinfo=user_tz)
            
            # Get the person's timezone and convert the time
            person_tz = person.get_timezone()
            meeting_datetime_person_tz = meeting_datetime.astimezone(person_tz)
            
            # Check availability
            is_available = one_on_one_manager.is_person_free(meeting_datetime_person_tz, email)
            
            # Format times for display
            user_time = meeting_datetime.strftime("%I:%M %p")
            user_date = meeting_datetime.strftime("%A, %B %d, %Y")
            person_time = meeting_datetime_person_tz.strftime("%I:%M %p")
            person_date = meeting_datetime_person_tz.strftime("%A, %B %d, %Y")
            
            # Display results
            click.echo("\n🕒 Availability Check:")
            click.echo("─" * 50)
            click.echo(f"Person:     {person.name}")
            click.echo(f"Your time:  {user_time} {user_tz}")
            click.echo(f"Your date:  {user_date}")
            if str(user_tz) != str(person_tz):
                click.echo(f"Their time: {person_time} {person_tz}")
                click.echo(f"Their date: {person_date}")
            click.echo("─" * 50)
            
            if is_available:
                click.echo("✅ Available for a 30-minute meeting")
            else:
                click.echo("❌ Not available (outside business hours or has conflicts)")
            click.echo("─" * 50)

        except ValueError as e:
            click.echo(f"❌ Error: {str(e)}")
            click.echo("\nPlease use the following format:")
            click.echo("  Date: YYYY-MM-DD (e.g., 2024-02-26)")
            click.echo("  Time: HH:MM in 24-hour format (e.g., 14:30)")

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {str(e)}")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")

@main.command()
@click.option('--start-date', '-s', type=str,
              help='Start date in YYYY-MM-DD format (defaults to next Monday)')
@click.option('--end-date', '-e', type=str,
              help='End date in YYYY-MM-DD format (defaults to next Friday)')
@click.option('--no-refresh', is_flag=True,
              help='Skip refreshing the dataset before recommending meetings')
@click.option('--dry-run', is_flag=True,
              help='Only simulate scheduling without actually creating calendar events')
@click.option('--org-file', '-o',
              default='calendar_manager/config/organization.csv',
              help='Path to the organization CSV file')
@click.option('--credentials', '-c',
              default='credentials.json',
              help='Path to the credentials.json file')
def recommend(start_date: Optional[str], end_date: Optional[str], no_refresh: bool, 
             dry_run: bool, org_file: str, credentials: str):
    """Recommend and confirm 1:1 meetings based on availability."""
    try:
        # Initialize dependencies
        person_manager = PersonManager(org_file)
        calendar_client = GoogleCalendarClient(credentials)

        # Get the organizer information
        with open('calendar_manager/config/meeting_frequency.yaml', 'r') as f:
            config = yaml.safe_load(f)
            organizer = Attendee(
                name=config['organizer']['name'],
                email=config['organizer']['email']
            )

        # Initialize the 1:1 manager
        one_on_one_manager = OneOnOneManager(
            organizer=organizer,
            person_manager=person_manager,
            calendar_client=calendar_client
        )

        # Refresh dataset by default unless --no-refresh is specified
        if not no_refresh:
            click.echo("\n🔄 Refreshing dataset of next meetings...")
            try:
                one_on_one_manager.refresh_next_meetings(days_back=60)
                click.echo("✅ Dataset refreshed successfully")
            except Exception as e:
                click.echo(f"⚠️  Failed to refresh dataset: {str(e)}")
                if not click.confirm("Continue with existing dataset?", default=True):
                    return

        # Parse dates if provided, otherwise use defaults
        start = None
        end = None
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                click.echo("❌ Invalid start date format. Please use YYYY-MM-DD")
                return
                
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                click.echo("❌ Invalid end date format. Please use YYYY-MM-DD")
                return

        if not start or not end:
            default_start, default_end = _get_default_date_range()
            if not start:
                start = default_start
            if not end:
                end = default_end

        # Get free slots
        click.echo("\n🔍 Finding available time slots...")
        slots = one_on_one_manager.get_free_slots(start_date=start, end_date=end)
        
        if not slots:
            click.echo("❌ No available time slots found in the specified date range.")
            return

        # Load next meetings data
        try:
            next_meetings = one_on_one_manager.load_next_meetings()
        except FileNotFoundError as e:
            click.echo(f"❌ {str(e)}")
            return

        if not next_meetings:
            click.echo("❌ No pending 1:1 meetings found.")
            return

        click.echo("\n📅 Checking availability and suggesting meetings...")
        click.echo("─" * 50)
        click.echo("Commands: 'y' to confirm, 'n' for next person, 's' to stop")
        click.echo("─" * 50)

        # For each slot
        for slot in slots:
            slot_time = slot.strftime("%A, %B %d at %I:%M %p")
            click.echo(f"\nChecking slot: {slot_time}")
            
            # For each person (already sorted by next meeting date)
            for email, next_date in next_meetings:
                person = person_manager.by_email(email)
                if not person:
                    continue

                if next_date.date() > end.date():
                    print(f"Skipping {person.name} because due date is after end date")
                    continue

                # Check if person is free
                try:
                    if one_on_one_manager.is_person_free(slot, email):
                        # Format the suggestion
                        person_tz = person.get_timezone()
                        local_time = slot.astimezone(person_tz)
                        
                        click.echo("\n📋 Suggested Meeting:")
                        click.echo("─" * 30)
                        click.echo(f"Person:     {person.name}")
                        click.echo(f"Your time:  {slot.strftime('%I:%M %p')} PT")
                        if str(person_tz) != "America/Los_Angeles":
                            click.echo(f"Their time: {local_time.strftime('%I:%M %p')} {person_tz}")
                        click.echo(f"Due date:   {next_date.strftime('%Y-%m-%d')}")
                        click.echo("─" * 30)
                        
                        # Get user confirmation
                        if click.confirm("Would you like to schedule this meeting?", default=True):
                            if dry_run:
                                click.echo("✅ Confirmed! (Dry run - no meeting scheduled)")
                            else:
                                try:
                                    # Schedule the meeting
                                    end_time = slot + timedelta(minutes=30)
                                    event = one_on_one_manager.schedule(email, slot, end_time)
                                    click.echo(f"✅ Meeting scheduled! Event ID: {event.id}")
                                except Exception as e:
                                    click.echo(f"❌ Failed to schedule meeting: {str(e)}")
                                    if not click.confirm("Continue with next suggestion?", default=True):
                                        return
                            # Remove this person from the list
                            next_meetings.remove((email, next_date))
                            # Move to next slot
                            break
                        elif click.confirm("Stop suggesting meetings?", default=False):
                            click.echo("\n👋 Stopping meeting suggestions.")
                            return
                        # If user says no, continue to next person
                        click.echo("Looking for next available person...")
                except ValueError as e:
                    click.echo(f"⚠️  Skipping {person.name}: {str(e)}")
                    continue

        # Show remaining people who still need meetings
        if next_meetings:
            click.echo("\n⚠️  People still needing meetings:")
            click.echo("─" * 30)
            for email, next_date in next_meetings:
                person = person_manager.by_email(email)
                if person:
                    click.echo(f"• {person.name} (due: {next_date.strftime('%Y-%m-%d')})")

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {str(e)}")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")