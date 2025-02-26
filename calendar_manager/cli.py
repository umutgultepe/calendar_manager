"""Command line interface for Calendar Manager."""

import os
import click
from .calendar_client import GoogleCalendarClient

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

if __name__ == '__main__':
    main() 