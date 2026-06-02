import datetime
import re
from google_auth import get_google_service
import google.generativeai as genai
import config

def get_calendar_service():
    """Returns a Google Calendar API service instance."""
    return get_google_service('calendar', 'v3')

def list_upcoming_events(max_results=10):
    """Lists the next N upcoming events on the user's primary calendar."""
    service = get_calendar_service()
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=now,
        maxResults=max_results, 
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

def parse_datetime_nl(text):
    """
    Parses a natural language time description into a python datetime object.
    Uses Gemini API if available, otherwise falls back to a regex heuristic.
    """
    now = datetime.datetime.now()
    
    # 1. Try to use Gemini API if key is available
    if config.GEMINI_API_KEY:
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = (
                f"You are a natural language parser helper for a calendar bot.\n"
                f"The current local date/time is: {now.strftime('%Y-%m-%d %H:%M:%S')} (weekday: {now.strftime('%A')}).\n"
                f"Given the text: '{text}', extract the following as a raw text string with format 'YYYY-MM-DD HH:MM:SS|title|description':\n"
                f"- The start date and time of the event (interpret terms like tomorrow, next Monday, etc. relative to current date/time).\n"
                f"- The title of the event (clean, short).\n"
                f"- A brief description of the event if any (otherwise 'None').\n"
                f"Response format: YYYY-MM-DD HH:MM:SS|title|description (ONLY return this text, nothing else, no formatting, no markdown)."
            )
            
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            parts = result.split('|')
            if len(parts) >= 2:
                dt_str = parts[0].strip()
                title = parts[1].strip()
                desc = parts[2].strip() if len(parts) > 2 else "Scheduled via Jarvis"
                
                parsed_dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                return parsed_dt, title, desc
        except Exception as e:
            print(f"Warning: Gemini NL parsing failed, falling back to regex: {e}")

    # 2. Heuristic Heuristic Regex Fallback
    # Pattern: "/calendar_add <title> at <YYYY-MM-DD HH:MM>" or "today HH:MM" or "tomorrow HH:MM"
    title = text.strip()
    desc = "Scheduled via Jarvis (Fallback parser)"
    
    # Look for " at " to separate title and time
    at_match = re.search(r'\s+at\s+(.+)$', text, re.IGNORECASE)
    if at_match:
        time_part = at_match.group(1).strip()
        title = text[:at_match.start()].strip()
        
        # Check YYYY-MM-DD HH:MM
        date_pattern = re.match(r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$', time_part)
        if date_pattern:
            parsed_dt = datetime.datetime.strptime(time_part, '%Y-%m-%d %H:%M')
            return parsed_dt, title, desc
            
        # Check "today HH:MM"
        today_pattern = re.match(r'^today\s+(\d{2}):(\d{2})$', time_part, re.IGNORECASE)
        if today_pattern:
            hour, minute = map(int, today_pattern.groups())
            parsed_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return parsed_dt, title, desc

        # Check "tomorrow HH:MM"
        tomorrow_pattern = re.match(r'^tomorrow\s+(\d{2}):(\d{2})$', time_part, re.IGNORECASE)
        if tomorrow_pattern:
            hour, minute = map(int, tomorrow_pattern.groups())
            tomorrow = now + datetime.timedelta(days=1)
            parsed_dt = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return parsed_dt, title, desc

    # Default to tomorrow at 10:00 AM if no match
    default_dt = (now + datetime.timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    return default_dt, title, desc

def create_calendar_event(summary, start_dt, duration_minutes=60, description=None):
    """Creates a new calendar event."""
    service = get_calendar_service()
    
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
    
    event_body = {
        'summary': summary,
        'description': description or 'Scheduled by Jarvis Bot',
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': datetime.datetime.now().astimezone().tzname() or 'UTC',
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': datetime.datetime.now().astimezone().tzname() or 'UTC',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 15},
            ],
        },
    }
    
    event = service.events().insert(calendarId='primary', body=event_body).execute()
    return event
