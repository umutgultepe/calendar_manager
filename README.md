# Calendar Manager CLI

A command-line interface application for managing calendars.

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Usage

After installation, you can use the CLI by running:

```bash
calendar-manager --help
```

### Available Commands

#### `validate-access`
Validate access to Google Calendar.
```bash
calendar-manager validate-access [OPTIONS]
Options:
  -c, --credentials TEXT  Path to the credentials.json file from Google Cloud Console
```

#### `get-last-by-username`
Find the last 1:1 meeting with a person by their username.
```bash
calendar-manager get-last-by-username USERNAME [OPTIONS]
Options:
  -d, --days INTEGER     Number of days to look back (default: 30)
  -o, --org-file TEXT   Path to the organization CSV file
  -c, --credentials TEXT  Path to the credentials.json file
```

#### `person`
Display information about a person by their email.
```bash
calendar-manager person EMAIL [OPTIONS]
Options:
  -o, --org-file TEXT   Path to the organization CSV file
```

#### `next-one-on-one`
Get the recommended date for the next 1:1 meeting with a person.
```bash
calendar-manager next-one-on-one USERNAME [OPTIONS]
Options:
  -d, --days INTEGER     Number of days to look back (default: 30)
  -o, --org-file TEXT   Path to the organization CSV file
  -c, --credentials TEXT  Path to the credentials.json file
```

#### `refresh-dataset`
Refresh the dataset of next recommended 1:1 meetings.
```bash
calendar-manager refresh-dataset [OPTIONS]
Options:
  -d, --days INTEGER     Number of days to look back (default: 60)
  -o, --org-file TEXT   Path to the organization CSV file
  -c, --credentials TEXT  Path to the credentials.json file
```

#### `free-slots`
Show available time slots for meetings in the specified date range.
```bash
calendar-manager free-slots [OPTIONS]
Options:
  -s, --start-date TEXT  Start date in YYYY-MM-DD format (defaults to next Monday)
  -e, --end-date TEXT    End date in YYYY-MM-DD format (defaults to next Friday)
  -o, --org-file TEXT    Path to the organization CSV file
  -c, --credentials TEXT Path to the credentials.json file
```

#### `is-free`
Check if a person is free for a 30-minute meeting.
```bash
calendar-manager is-free USERNAME DATE TIME [OPTIONS]
Arguments:
  USERNAME              Username (without domain)
  DATE                 Date in YYYY-MM-DD format
  TIME                 Time in HH:MM format (24-hour) in YOUR timezone
Options:
  -o, --org-file TEXT    Path to the organization CSV file
  -c, --credentials TEXT Path to the credentials.json file
```

#### `recommend`
Recommend and confirm 1:1 meetings based on availability.
```bash
calendar-manager recommend [OPTIONS]
Options:
  -s, --start-date TEXT  Start date in YYYY-MM-DD format (defaults to next Monday)
  -e, --end-date TEXT    End date in YYYY-MM-DD format (defaults to next Friday)
  --no-refresh          Skip refreshing the dataset before recommending meetings
  -o, --org-file TEXT    Path to the organization CSV file
  -c, --credentials TEXT Path to the credentials.json file
```

## Development

To run tests:
```bash
pytest
```

## License

MIT

## TODO
- Add scheduling support
- Meeting is not eligible if it hasn't been enough time yet.