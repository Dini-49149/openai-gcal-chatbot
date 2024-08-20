from flask import Flask, request, jsonify, render_template, redirect, url_for
import openai
import json
import os
import pickle
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timezone
import pytz

app = Flask(__name__)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']

@app.route('/')
def home():
    return render_template('chat.html')

def get_api_key(file_path, key):
    with open(file_path, 'r') as file:
        data = json.load(file)
        api_key = data.get(key)
        return api_key

def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are not valid or not available, start the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
            flow.redirect_uri = url_for('oauth2callback', _external=True)
            authorization_url, _ = flow.authorization_url(prompt='consent')
            return authorization_url  # Return the authorization URL
    service = build('calendar', 'v3', credentials=creds)
    return service

@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    return redirect(url_for('home'))

@app.route('/authenticate', methods=['GET'])
def authenticate():
    auth_url = authenticate_google_calendar()
    if isinstance(auth_url, str):
        return jsonify({'auth_url': auth_url})
    return jsonify({'message': 'Your Google Account Authenticated Successfully!'})

def convert_utc_to_est(utc_time_str):
    """Convert UTC time to EST"""
    utc = pytz.utc
    est = pytz.timezone('US/Eastern')
    
    # Parse the UTC time string to a datetime object (with timezone info)
    utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
    
    # Convert UTC time to EST
    est_time = utc_time.astimezone(est)
    
    # Return the EST time in the same format
    return est_time.strftime('%Y-%m-%dT%H:%M:%S')


def list_events():
    service = authenticate_google_calendar()
    if isinstance(service, str):
        return service  # Return auth_url if authentication is required

    now = datetime.now(timezone.utc).isoformat()
    events_result = service.events().list(calendarId='primary', maxResults=10, singleEvents=True,
                                          orderBy='startTime', timeMin=now).execute()
    events = events_result.get('items', [])
    
    if not events:
        return "No upcoming events found."
    
    events_str = "Upcoming Events:<br><br>"
    for event in events:
        event_id = event.get('id', 'No ID')
        summary = event.get('summary', 'No Title')
        description = event.get('description', 'No Description')
        
        # Get start and end time of the event in UTC
        start_time_str = event['start'].get('dateTime', event['start'].get('date'))
        end_time_str = event['end'].get('dateTime', event['end'].get('date'))

        # Convert UTC to EST for display
        start_time_est = convert_utc_to_est(start_time_str)
        end_time_est = convert_utc_to_est(end_time_str)

        # Convert start_time_est to datetime for further processing
        start_time = datetime.strptime(start_time_est, '%Y-%m-%dT%H:%M:%S')
        end_time = datetime.strptime(end_time_est, '%Y-%m-%dT%H:%M:%S')

        # Calculate event duration in minutes
        duration = int((end_time - start_time).total_seconds() / 60)

        # Format the date and time in EST
        date = start_time.strftime("%Y-%m-%d")
        time = start_time.strftime("%I:%M %p")  # 12-hour format with AM/PM
        
        events_str += f"<strong>Title</strong>: {summary}<br>"
        events_str += f"<strong>Date</strong>: {date}<br>"
        events_str += f"<strong>Start Time</strong>: {time}<br>"
        events_str += f"<strong>Duration</strong>: {duration} mins<br>"
        events_str += f"<strong>Description</strong>: {description}<br>"
        events_str += f"<strong>ID</strong>: {event_id}<br><br>"
    return events_str

def convert_est_to_utc(est_time_str):
    """Convert EST time to UTC"""
    est = pytz.timezone('US/Eastern')
    utc = pytz.utc
    
    # Parse the EST time string
    est_time = est.localize(datetime.strptime(est_time_str, '%Y-%m-%dT%H:%M:%SZ'))
    
    # Convert EST time to UTC
    utc_time = est_time.astimezone(utc)
    
    # Return the UTC time in the same format
    return utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')

def create_event(summary, location, description, start_time, end_time, timezone, attendees_emails):
    service = authenticate_google_calendar()
    if isinstance(service, str):
        return service  # Return auth_url if authentication is required

    # Convert EST to UTC before sending to Google Calendar
    start_time_utc = convert_est_to_utc(start_time)
    end_time_utc = convert_est_to_utc(end_time)

    attendees = [{'email': email.strip()} for email in attendees_emails.split(",") if email]
    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_time_utc,
            'timeZone': 'UTC',  # Ensure timezone is set to UTC
        },
        'end': {
            'dateTime': end_time_utc,
            'timeZone': 'UTC',  # Ensure timezone is set to UTC
        },
        'attendees': attendees,
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
        'conferenceData': {
            'createRequest': {
                'requestId': 'sample123',
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet'
                }
            }
        }
    }
    try:
        created_event = service.events().insert(calendarId='primary', body=event, conferenceDataVersion=1, sendUpdates='all').execute()
        return f"Event created successfully with <strong>id</strong> : <strong>{created_event.get('id')}</strong>"
    except Exception as e:
        return f"Failed to create an event. Error: {e}"

def update_event(event_id, summary, location, description, start_time, end_time, timezone, attendees_emails):
    service = authenticate_google_calendar()
    if isinstance(service, str):
        return service  # Return auth_url if authentication is required

    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    event['summary'] = summary or event['summary']
    event['location'] = location or event.get('location', '')
    event['description'] = description or event.get('description', '')
    event['start']['dateTime'] = start_time or event['start']['dateTime']
    event['end']['dateTime'] = end_time or event['end']['dateTime']
    event['start']['timeZone'] = timezone or event['start']['timeZone']
    event['end']['timeZone'] = timezone or event['end']['timeZone']
    attendees = [{'email': email.strip()} for email in attendees_emails.split(",") if email]
    event['attendees'] = attendees or event.get('attendees', [])
    try:
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return "Event has been updated successfully!"
    except Exception as e:
        return f"Failed to update the event. Error: {e}"

def delete_event(event_id):
    service = authenticate_google_calendar()
    if isinstance(service, str):
        return service  # Return auth_url if authentication is required
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return "Event deleted successfully."
    except:
        return "Error occurred in deleting an event!"

# Define the function descriptions for OpenAI
functions = [
    {
        "name": "list_events",
        "description": "List upcoming Google Calendar events",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_event",
        "description": "Create a new event in Google Calendar",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event Title"},
                "location": {"type": "string", "description": "Location"},
                "description": {"type": "string", "description": "Description"},
                "start_time": {"type": "string", "description": "Start Time (YYYY-MM-DDTHH:MM:SSZ)"},
                "end_time": {"type": "string", "description": "End Time (YYYY-MM-DDTHH:MM:SSZ)"},
                "timezone": {"type": "string", "description": "Timezone"},
                "attendees_emails": {"type": "string", "description": "Comma-separated Attendee Emails"}
            },
            "required": ["summary", "start_time", "end_time", "timezone"]
        }
    },
    {
        "name": "update_event",
        "description": "Update an existing Google Calendar event",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event ID"},
                "summary": {"type": "string", "description": "New Event Title"},
                "location": {"type": "string", "description": "New Location"},
                "description": {"type": "string", "description": "New Description"},
                "start_time": {"type": "string", "description": "New Start Time (YYYY-MM-DDTHH:MM:SSZ)"},
                "end_time": {"type": "string", "description": "New End Time (YYYY-MM-DDTHH:MM:SSZ)"},
                "timezone": {"type": "string", "description": "Timezone"},
                "attendees_emails": {"type": "string", "description": "New Comma-separated Attendee Emails"}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "delete_event",
        "description": "Delete a Google Calendar event",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event ID to Delete"}
            },
            "required": ["event_id"]
        }
    }
]

@app.route('/chat', methods=['POST'])
def chat():
    global conversation_history
    user_input = request.json['message']
    conversation_history.append({"role": "user", "content": user_input})
    
    openai.api_key = OPENAI_API_KEY

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        functions=functions,
        function_call="auto"
    )
    
    message = response["choices"][0]["message"]

    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        function_args = json.loads(message["function_call"]["arguments"])
        
        if function_name == "list_events":
            result = list_events()
            conversation_history.append({"role": "assistant", "content": result})
            return jsonify({"response": result})

        elif function_name == "create_event":
            result = create_event(function_args["summary"], function_args.get("location", ""), function_args.get("description", ""), 
                                  function_args["start_time"], function_args["end_time"], function_args["timezone"], 
                                  function_args.get("attendees_emails", ""))
            conversation_history.append({"role": "assistant", "content": result})
            return jsonify({"response": result})

        elif function_name == "update_event":
            result = update_event(function_args["event_id"], function_args.get("summary", ""), function_args.get("location", ""), 
                                  function_args.get("description", ""), function_args.get("start_time", ""), 
                                  function_args.get("end_time", ""), function_args.get("timezone", ""), 
                                  function_args.get("attendees_emails", ""))
            conversation_history.append({"role": "assistant", "content": result})
            return jsonify({"response": result})

        elif function_name == "delete_event":
            result = delete_event(function_args["event_id"])
            conversation_history.append({"role": "assistant", "content": result})
            return jsonify({"response": result})
    else:
        conversation_history.append({"role": "assistant", "content": message["content"]})
        return jsonify({"response": message["content"]})

if __name__ == '__main__':
    global conversation_history, OPENAI_API_KEY
    conversation_history = []
    OPENAI_API_KEY = get_api_key('api_key.json', 'openai_api_key')
    app.run(debug=True)
