"""Command line interface for Calendar Manager."""

import os
import yaml
import click
from datetime import datetime
from .calendar_client import GoogleCalendarClient
from .person_manager import PersonManager
from .one_on_one_manager import OneOnOneManager
from .models import Attendee

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
        organizer = Attendee(
            name="Umut Gultepe",  # This should be your name
            email="ugultepe@abnormalsecurity.com"  # This should be your email
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
        manager = PersonManager(org_file)
        person = manager.by_email(email + '@abnormalsecurity.com')
        
        if not person:
            click.echo(f"❌ No person found with email: {email}@abnormalsecurity.com")
            return
        
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
        click.echo("─" * 50)
        
    except FileNotFoundError:
        click.echo(f"❌ Organization file not found at: {org_file}")
    except Exception as e:
        click.echo(f"❌ Error retrieving person information: {str(e)}")

if __name__ == '__main__':
    main() 