from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

SCOPES_REQUIRED = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]
    

def merge_calendars(source_calendars, dest_calendar, service_account_file,
        censor=False, censor_name="Busy", delete=True, do_not_include=None):
    """
    Merges two google calendar's into another (by default, the second one)

    Parameters:
    - source_calendars : A list-like of Strings containing calendar IDs of the
      calendars to be merged
    - dest_calendar: A string with the calendar ID of the destination of the
      merged calendar
    - serice_account_file: JSON file containing service account credentials
    - censor: Whether to censor the event title, description, and 
    - censor_name: If censored, name the event this
    - delete: If an event is in dest_calendar but none of
      source_calendars, delete it?
    - do_not_include: a pattern or list of patterns when matched in either the
      title or description of an event, do not include in the merge
    """
    
    # Get credentials from credential file
    creds = None
    creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES_REQUIRED)

    # Format source_calendars correctly
    if isinstance(source_calendars, str):
        source_calendars = [source_calendars]
    
    # format do_not_include into single pattern
    if not isinstance(do_not_include, str):
        do_not_include = "(" + ")|(".join(do_not_include) + ")"

    try:
        # Connect to Google API
        service = build('calendar', 'v3', credentials=creds)

        # Get Source Events
        source_events = []
        for source in source_calendars:
            source_events += _get_events(source, service)

        # Get Destination Events
        dest_events = _get_events(dest_calendar, service)

        # Filter source events that don't have start, end, and title
        source_events = [
            event for event in source_events
            if not (    event.get('start', None) 
                    and event.get('end', None) 
                    and event.get('start', None))
        ]

        # Filter source events that match do_not_include
        source_events = [
            event for event in source_events
            if (    re.match(do_not_include, event.get('summary'))
                 or re.match(do_not_include, event.get('description')))
        ]

        # TODO Remove event organizer and creator
        for event in source_events:
            del event['creator']
            del event['organizer']

        # Censor source events
        if censor:
            for event in source_events:
                event['summary'] = censor_name
                event['description'] = ""
                del event['location']

        # Find dest events not in source events
        remove_events = []
        for dest_event in dest_events:
            found_event = False
            for source_event in source_events:
                if (    dest_event.get('summary', None) 
                            == source_event.get('summary', None)
                    and dest_event.get('start', None) 
                            == source_event.get('start', None)
                    and dest_event.get('end', None) 
                            == source_event.get('end', None)):
                    
                    found_event = True
                    break

            if found_event:
                continue

            remove_events.append(dest_event)

        # Filter source events already in destination
        for source_event in source_events:
            found_event = False
            for dest_event in dest_events:
                if (    dest_event.get('summary', None) 
                            == source_event.get('summary', None)
                    and dest_event.get('start', None) 
                            == source_event.get('start', None)
                    and dest_event.get('end', None) 
                            == source_event.get('end', None)):
                    
                    found_event = True
                    break

            if found_event:
                continue

            source_events.remove(source_event)

        # Add Source Events not in Destination events
        _add_events(dest_calendar, source_events, service) 

        # Delete destination events not in source events
        if delete_events:
            _delete_events(dest_calendar, remove_events, service)

    except HttpError as err:
        print(err)

def _add_events(calendarId, events, service):
    "Adds events to a calendar"
    if isinstance(events, dict):
        service.events().import_(calendarId=calendarId, body=events).execute()
    else:
        try:
            for event in events:
                service.events().import_(calendarId=calendarId, body=event).execute()
        except TypeError:
            print(err)

def _delete_events(calendarId, events, service):
    "Removes events from a calendar"
    if isinstance(events, dict):
        service.events().delete(calendarId=calendarId, body=events).execute()
    else:
        try:
            for event in events:
                service.events().delete(calendarId=calendarId, body=event).execute()
        except TypeError:
            print(err)

def _get_events(calendarId, service):
    "Gets events from a calendar"
    events = []
    page_token = None
    while True:
        events_page = service.events().list(
                calendarId=calendarId,pageToken=page_token).execute()
        page_token = events_page.get('nextPageToken')
        events += events_page['items']
        if not page_token:
          break
    return events
