import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class GoogleMeetService:
    """Google Meet service for creating Meet links via Google Calendar API"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self, user):
        self.user = user
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar API service with user credentials"""
        try:
            credentials = self._get_user_credentials()
            if credentials and credentials.valid:
                self.service = build('calendar', 'v3', credentials=credentials)
            elif credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._save_user_credentials(credentials)
                self.service = build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Error initializing Google Calendar service: {e}")
            self.service = None
    
    def _get_user_credentials(self) -> Optional[Credentials]:
        """Get stored credentials for the user"""
        try:
            from mobilize.authentication.models import GoogleToken
            token = GoogleToken.objects.filter(user=self.user).first()
            if token and token.access_token:
                # Use the actual stored scopes instead of hardcoded ones
                stored_scopes = token.scopes if token.scopes else self.SCOPES
                creds_data = {
                    'token': token.access_token,
                    'refresh_token': token.refresh_token,
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'scopes': stored_scopes
                }
                return Credentials.from_authorized_user_info(creds_data)
        except Exception as e:
            print(f"Error getting user credentials: {e}")
        return None
    
    def _save_user_credentials(self, credentials: Credentials):
        """Save updated credentials for the user"""
        try:
            from mobilize.authentication.models import GoogleToken
            token, created = GoogleToken.objects.get_or_create(user=self.user)
            token.access_token = credentials.token
            token.refresh_token = credentials.refresh_token
            token.expires_at = credentials.expiry
            token.save()
        except Exception as e:
            print(f"Error saving user credentials: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user has valid Google Calendar credentials"""
        return self.service is not None
    
    def create_instant_meet_link(self, title: str = "Video Call", duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Create an instant Google Meet link by creating a calendar event
        
        Args:
            title: Title for the calendar event
            duration_minutes: Duration of the meeting in minutes
            
        Returns:
            Dict with success status, meet_link, and event_id
        """
        if not self.service:
            return {'success': False, 'error': 'Google Calendar service not authenticated'}
        
        try:
            # Create event starting now
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': title,
                'description': f'Video call created via Mobilize CRM at {start_time.strftime("%Y-%m-%d %H:%M")}',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/New_York',  # You might want to make this configurable
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meet_{int(start_time.timestamp())}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'attendees': [
                    {'email': self.user.email}
                ]
            }
            
            # Create the event with Meet link
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            # Extract Meet link
            meet_link = None
            if 'conferenceData' in created_event and 'entryPoints' in created_event['conferenceData']:
                for entry_point in created_event['conferenceData']['entryPoints']:
                    if entry_point['entryPointType'] == 'video':
                        meet_link = entry_point['uri']
                        break
            
            return {
                'success': True,
                'meet_link': meet_link,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'title': title,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
        except HttpError as error:
            return {'success': False, 'error': f'Google Calendar API error: {error}'}
        except Exception as error:
            return {'success': False, 'error': f'Unexpected error: {error}'}
    
    def create_scheduled_meet(self, title: str, start_datetime: datetime, 
                            end_datetime: datetime, description: str = "",
                            attendee_emails: list = None) -> Dict[str, Any]:
        """
        Create a scheduled Google Meet link for a future time
        
        Args:
            title: Title for the calendar event
            start_datetime: When the meeting starts
            end_datetime: When the meeting ends
            description: Description for the meeting
            attendee_emails: List of email addresses to invite
            
        Returns:
            Dict with success status, meet_link, and event_id
        """
        if not self.service:
            return {'success': False, 'error': 'Google Calendar service not authenticated'}
        
        try:
            attendees = [{'email': self.user.email}]
            if attendee_emails:
                attendees.extend([{'email': email} for email in attendee_emails])
            
            event = {
                'summary': title,
                'description': description or f'Video call scheduled via Mobilize CRM',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meet_{int(start_datetime.timestamp())}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                },
                'attendees': attendees
            }
            
            # Create the event with Meet link
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            # Extract Meet link
            meet_link = None
            if 'conferenceData' in created_event and 'entryPoints' in created_event['conferenceData']:
                for entry_point in created_event['conferenceData']['entryPoints']:
                    if entry_point['entryPointType'] == 'video':
                        meet_link = entry_point['uri']
                        break
            
            return {
                'success': True,
                'meet_link': meet_link,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'title': title,
                'start_time': start_datetime.isoformat(),
                'end_time': end_datetime.isoformat()
            }
            
        except HttpError as error:
            return {'success': False, 'error': f'Google Calendar API error: {error}'}
        except Exception as error:
            return {'success': False, 'error': f'Unexpected error: {error}'}