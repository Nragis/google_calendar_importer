import os
 
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events',
        ]
SERVICE_ACCOUNT_FILE = 'calendar-merger-service-key.json'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

merged_calendar_key = "8709d173fbdcd0312ab472328d998ffa4a5a8336240140af305217245f7b67f8@group.calendar.google.com"
source_calendar_keys = [
    "quinn@qmurph.me",
    "59bfddfd4e96a05112b31315a9d832adb87be8a4e51ccd3c60dbb46ad0dfac33@group.calendar.google.com",
    "quinn@highergroundlearning.com",
    "cqskd0evpi60hhbr2noivd37bk@group.calendar.google.com"
  ]

def lambda_handler(event, context): 
    creds = None
    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    try:
        service = build('calendar', 'v3', credentials=creds)
        source_events = []
        for source_calendar_key in source_calendar_keys:
            page_token = None
            while True:
                events = service.events().list(calendarId=source_calendar_key,pageToken=page_token).execute()
                page_token = events.get('nextPageToken')
                source_events += events['items']
                if not page_token:
                  break
        merged_events = []
        page_token = None
        while True:
            events = service.events().list(calendarId=merged_calendar_key,pageToken=page_token).execute()
            page_token = events.get('nextPageToken')
            merged_events += events['items']
            if not page_token:
              break

        source_events = [ event for event in source_events if
                (event.get('summary', None) and event.get('summary', None)
                    and event.get('summary', None))]

        for event in source_events:
            if event.get('end', None) and event.get('start', None):
                c = False
                for m_event in merged_events:
                    if event['summary'] == m_event['summary'] \
                            and event['start'] == m_event['start'] \
                            and event['end'] == m_event['end']:
                                c = True
                                break
                if c == True:
                    continue
                old_organizer = event['organizer']['email']
                event['organizer']['email'] = merged_calendar_key
                if event not in merged_events:
                    print(f"Imported {event['summary']} from {old_organizer}")
                    service.events().import_(calendarId=merged_calendar_key, body=event).execute()

        for event in merged_events:
            if not (event.get('summary', None) and event.get('start', None) \
                    and event.get('end', None)):
                print(f"Removed _")
                service.events().delete(calendarId=merged_calendar_key, eventId=event['id']).execute()
                continue

            c = False
            for s_event in source_events:
                if event['summary'] == s_event['summary'] \
                        and event['start'] == s_event['start'] \
                        and event['end'] == s_event['end']:
                            c = True
                            break
            if c == False:
                print(f"Removed {event['summary']}")
                service.events().delete(calendarId=merged_calendar_key, eventId=event['id']).execute()

    except HttpError as err:
        print(err)


if __name__ == '__main__':
    lambda_handler(None, None)
