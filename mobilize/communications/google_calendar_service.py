import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class GoogleCalendarService:
    """Google Calendar API service for managing events and calendar integration"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self, user):
        self.user = user
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Calendar API service with user credentials"""
        try:
            credentials = self._get_user_credentials()
            if credentials and credentials.valid:
                self.service = build('calendar', 'v3', credentials=credentials)
            elif credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._save_user_credentials(credentials)
                self.service = build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Error initializing Calendar service: {e}")
            self.service = None
    
    def _get_user_credentials(self) -> Optional[Credentials]:
        """Get stored credentials for the user"""
        try:
            from mobilize.authentication.models import GoogleToken
            token = GoogleToken.objects.filter(user=self.user).first()
            if token and token.access_token:
                # Use the user's actual scopes, not the service's required scopes
                user_scopes = token.scopes if token.scopes else self.SCOPES
                creds_data = {
                    'token': token.access_token,
                    'refresh_token': token.refresh_token,
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'scopes': user_scopes
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
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """Get Calendar authorization URL for OAuth flow"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return authorization_url
    
    def handle_oauth_callback(self, authorization_code: str, redirect_uri: str):
        """Handle OAuth callback and store credentials"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = redirect_uri
        
        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials
        
        self._save_user_credentials(credentials)
        self._initialize_service()
        
        return credentials
    
    def is_authenticated(self) -> bool:
        """Check if user has valid Calendar credentials"""
        return self.service is not None
    
    def get_calendars(self) -> List[Dict]:
        """Get list of user's calendars"""
        if not self.service:
            return []
        
        try:
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            return [{
                'id': calendar['id'],
                'summary': calendar['summary'],
                'description': calendar.get('description', ''),
                'primary': calendar.get('primary', False),
                'access_role': calendar.get('accessRole', 'reader'),
                'color_id': calendar.get('colorId', '1')
            } for calendar in calendars]
            
        except HttpError as error:
            print(f'Calendar API error: {error}')
            return []
    
    def create_event(self, 
                     calendar_id: str,
                     title: str,
                     description: str,
                     start_datetime: datetime,
                     end_datetime: datetime,
                     attendees: Optional[List[str]] = None,
                     location: Optional[str] = None,
                     timezone_name: str = 'UTC',
                     all_day: bool = False,
                     recurrence: Optional[List[str]] = None,
                     reminders: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a calendar event"""
        
        if not self.service:
            return {'success': False, 'error': 'Calendar service not authenticated'}
        
        try:
            # Convert timezone
            user_tz = pytz.timezone(timezone_name)
            
            if all_day:
                # For all-day events, use date format
                event_start = {'date': start_datetime.date().isoformat()}
                event_end = {'date': end_datetime.date().isoformat()}
            else:
                # For timed events, use dateTime format
                if start_datetime.tzinfo is None:
                    start_datetime = user_tz.localize(start_datetime)
                if end_datetime.tzinfo is None:
                    end_datetime = user_tz.localize(end_datetime)
                
                event_start = {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': timezone_name
                }
                event_end = {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': timezone_name
                }
            
            # Build event object
            event = {
                'summary': title,
                'description': description,
                'start': event_start,
                'end': event_end,
            }
            
            if location:
                event['location'] = location
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            if recurrence:
                event['recurrence'] = recurrence
            
            # Set reminders
            if reminders:
                event['reminders'] = reminders
            else:
                # Default reminders
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 minutes before
                    ],
                }
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            # Create communication record
            self._create_communication_record(
                title=title,
                description=description,
                start_datetime=start_datetime,
                event_id=created_event.get('id'),
                event_link=created_event.get('htmlLink'),
                attendees=attendees or []
            )
            
            return {
                'success': True,
                'event_id': created_event.get('id'),
                'event_link': created_event.get('htmlLink'),
                'event': created_event
            }
            
        except HttpError as error:
            return {'success': False, 'error': f'Calendar API error: {error}'}
        except Exception as error:
            return {'success': False, 'error': f'Unexpected error: {error}'}
    
    def update_event(self, 
                     calendar_id: str,
                     event_id: str,
                     title: Optional[str] = None,
                     description: Optional[str] = None,
                     start_datetime: Optional[datetime] = None,
                     end_datetime: Optional[datetime] = None,
                     attendees: Optional[List[str]] = None,
                     location: Optional[str] = None) -> Dict[str, Any]:
        """Update an existing calendar event"""
        
        if not self.service:
            return {'success': False, 'error': 'Calendar service not authenticated'}
        
        try:
            # Get the existing event
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if title is not None:
                event['summary'] = title
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            if attendees is not None:
                event['attendees'] = [{'email': email} for email in attendees]
            
            if start_datetime and end_datetime:
                if 'date' in event['start']:
                    # All-day event
                    event['start']['date'] = start_datetime.date().isoformat()
                    event['end']['date'] = end_datetime.date().isoformat()
                else:
                    # Timed event
                    event['start']['dateTime'] = start_datetime.isoformat()
                    event['end']['dateTime'] = end_datetime.isoformat()
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': updated_event.get('id'),
                'event_link': updated_event.get('htmlLink'),
                'event': updated_event
            }
            
        except HttpError as error:
            return {'success': False, 'error': f'Calendar API error: {error}'}
        except Exception as error:
            return {'success': False, 'error': f'Unexpected error: {error}'}
    
    def delete_event(self, calendar_id: str, event_id: str) -> Dict[str, Any]:
        """Delete a calendar event"""
        
        if not self.service:
            return {'success': False, 'error': 'Calendar service not authenticated'}
        
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return {'success': True}
            
        except HttpError as error:
            return {'success': False, 'error': f'Calendar API error: {error}'}
        except Exception as error:
            return {'success': False, 'error': f'Unexpected error: {error}'}
    
    def get_events(self, 
                   calendar_id: str = 'primary',
                   time_min: Optional[datetime] = None,
                   time_max: Optional[datetime] = None,
                   max_results: int = 10) -> List[Dict]:
        """Get calendar events"""
        
        if not self.service:
            return []
        
        try:
            # Set default time range if not provided
            if time_min is None:
                time_min = datetime.now(pytz.UTC)
            if time_max is None:
                time_max = time_min + timedelta(days=30)
            
            # Ensure timezone awareness
            if time_min.tzinfo is None:
                time_min = pytz.UTC.localize(time_min)
            if time_max.tzinfo is None:
                time_max = pytz.UTC.localize(time_max)
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return [{
                'id': event['id'],
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start': event['start'],
                'end': event['end'],
                'location': event.get('location', ''),
                'attendees': event.get('attendees', []),
                'html_link': event.get('htmlLink', ''),
                'creator': event.get('creator', {}),
                'organizer': event.get('organizer', {}),
                'status': event.get('status', 'confirmed')
            } for event in events]
            
        except HttpError as error:
            print(f'Calendar API error: {error}')
            return []
    
    def sync_events_to_tasks(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Sync calendar events to task system"""
        if not self.service:
            return {'success': False, 'error': 'Calendar service not authenticated'}
        
        from mobilize.tasks.models import Task
        from datetime import datetime, timedelta
        
        # Get events for the next specified days
        time_min = datetime.now(pytz.UTC)
        time_max = time_min + timedelta(days=days_ahead)
        
        events = self.get_events(
            calendar_id='primary',
            time_min=time_min,
            time_max=time_max,
            max_results=100
        )
        
        synced_count = 0
        
        for event in events:
            # Check if task already exists for this event
            if not Task.objects.filter(
                google_calendar_event_id=event['id']
            ).exists():
                
                # Parse start time
                start_info = event['start']
                if 'dateTime' in start_info:
                    due_date = datetime.fromisoformat(start_info['dateTime'].replace('Z', '+00:00')).date()
                else:
                    due_date = datetime.fromisoformat(start_info['date']).date()
                
                # Create task from calendar event
                Task.objects.create(
                    title=event['summary'],
                    description=event.get('description', ''),
                    due_date=due_date,
                    assigned_to=self.user,
                    created_by=self.user,
                    google_calendar_event_id=event['id'],
                    status='pending',
                    priority='medium'
                )
                synced_count += 1
        
        return {'success': True, 'synced_count': synced_count}
    
    def _create_communication_record(self, **kwargs):
        """Create a communication record for calendar event"""
        try:
            from mobilize.communications.models import Communication
            
            Communication.objects.create(
                type='meeting',
                subject=kwargs['title'],
                message=kwargs['description'],
                direction='outbound',
                date=kwargs['start_datetime'].date(),
                date_sent=timezone.now(),
                google_calendar_event_id=kwargs.get('event_id'),
                google_meet_link=kwargs.get('event_link'),
                user=self.user
            )
        except Exception as e:
            print(f"Error creating communication record: {e}")
    
    def get_free_busy(self, 
                      calendar_ids: List[str],
                      time_min: datetime,
                      time_max: datetime) -> Dict[str, Any]:
        """Get free/busy information for calendars"""
        
        if not self.service:
            return {'success': False, 'error': 'Calendar service not authenticated'}
        
        try:
            # Ensure timezone awareness
            if time_min.tzinfo is None:
                time_min = pytz.UTC.localize(time_min)
            if time_max.tzinfo is None:
                time_max = pytz.UTC.localize(time_max)
            
            body = {
                'timeMin': time_min.isoformat(),
                'timeMax': time_max.isoformat(),
                'items': [{'id': cal_id} for cal_id in calendar_ids]
            }
            
            freebusy = self.service.freebusy().query(body=body).execute()
            
            return {
                'success': True,
                'calendars': freebusy.get('calendars', {}),
                'time_min': time_min.isoformat(),
                'time_max': time_max.isoformat()
            }
            
        except HttpError as error:
            return {'success': False, 'error': f'Calendar API error: {error}'}
        except Exception as error:
            return {'success': False, 'error': f'Unexpected error: {error}'}
    
    def create_event_from_task(self, task, calendar_id: str = 'primary') -> Dict[str, Any]:
        """Create a Google Calendar event from a Task object"""
        if not self.service:
            return {'success': False, 'error': 'Calendar service not authenticated'}
        
        if not task.due_date:
            return {'success': False, 'error': 'Task must have a due date to create calendar event'}
        
        try:
            # Prepare event details
            title = task.title or f"Task: {task.id}"
            description = task.description or ""
            
            # Add task details to description
            task_details = f"\n\nTask Details:\n"
            task_details += f"Priority: {task.get_priority_display()}\n"
            task_details += f"Status: {task.get_status_display()}\n"
            if task.assigned_to:
                task_details += f"Assigned to: {task.assigned_to.get_full_name() or task.assigned_to.username}\n"
            if task.person:
                task_details += f"Related to: {task.person}\n"
            if task.church:
                task_details += f"Church: {task.church}\n"
            
            description += task_details
            
            # Calculate start and end times
            if task.due_time:
                # Parse due_time if it's a string
                if isinstance(task.due_time, str):
                    try:
                        from datetime import datetime as dt
                        due_time_obj = dt.strptime(task.due_time, '%H:%M').time()
                    except ValueError:
                        due_time_obj = dt.strptime('09:00', '%H:%M').time()  # Default to 9 AM
                else:
                    due_time_obj = task.due_time
                
                # Create datetime objects
                start_datetime = datetime.combine(task.due_date, due_time_obj)
                end_datetime = start_datetime + timedelta(hours=1)  # Default 1 hour duration
                all_day = False
            else:
                # All-day event
                start_datetime = datetime.combine(task.due_date, datetime.min.time())
                end_datetime = start_datetime + timedelta(days=1)
                all_day = True
            
            # Handle recurrence if this is a recurring task template
            recurrence_rules = None
            if task.is_recurring_template and task.recurring_pattern:
                recurrence_rules = self._convert_task_recurrence_to_rrule(task)
            
            # Create the calendar event
            result = self.create_event(
                calendar_id=calendar_id,
                title=title,
                description=description,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                all_day=all_day,
                timezone_name=str(timezone.get_current_timezone()),
                recurrence=recurrence_rules,
                reminders={
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30},  # 30 minutes before
                    ],
                }
            )
            
            if result['success']:
                # Update the task with calendar event information
                task.google_calendar_event_id = result['event_id']
                task.last_synced_at = timezone.now()
                task.save(update_fields=['google_calendar_event_id', 'last_synced_at'])
                
                return {
                    'success': True,
                    'event_id': result['event_id'],
                    'event_link': result['event_link'],
                    'message': f'Calendar event created successfully for task: {task.title}'
                }
            else:
                return result
                
        except Exception as error:
            return {'success': False, 'error': f'Error creating calendar event from task: {error}'}
    
    def _convert_task_recurrence_to_rrule(self, task) -> List[str]:
        """Convert task recurring pattern to Google Calendar RRULE format"""
        try:
            pattern = task.recurring_pattern
            frequency = pattern.get('frequency')
            interval = pattern.get('interval', 1)
            
            if not frequency:
                return None
            
            # Build RRULE string
            rrule_parts = []
            
            # Frequency mapping
            freq_map = {
                'daily': 'DAILY',
                'weekly': 'WEEKLY', 
                'monthly': 'MONTHLY'
            }
            
            if frequency not in freq_map:
                return None
                
            rrule_parts.append(f"FREQ={freq_map[frequency]}")
            
            # Interval
            if interval > 1:
                rrule_parts.append(f"INTERVAL={interval}")
            
            # Weekly: specific days
            if frequency == 'weekly' and pattern.get('weekdays'):
                # Convert from task format (0=Mon) to RRULE format (MO, TU, etc.)
                day_map = {0: 'MO', 1: 'TU', 2: 'WE', 3: 'TH', 4: 'FR', 5: 'SA', 6: 'SU'}
                weekdays = [day_map[day] for day in pattern['weekdays'] if day in day_map]
                if weekdays:
                    rrule_parts.append(f"BYDAY={','.join(weekdays)}")
            
            # Monthly: specific day of month
            if frequency == 'monthly' and pattern.get('day_of_month'):
                rrule_parts.append(f"BYMONTHDAY={pattern['day_of_month']}")
            
            # End date
            if task.recurrence_end_date:
                # Convert to RRULE format: YYYYMMDD
                end_date_str = task.recurrence_end_date.strftime('%Y%m%d')
                rrule_parts.append(f"UNTIL={end_date_str}")
            
            # Build final RRULE
            rrule = "RRULE:" + ";".join(rrule_parts)
            
            return [rrule]
            
        except Exception as e:
            print(f"Error converting recurrence to RRULE: {e}")
            return None