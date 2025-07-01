import os
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Communication, EmailTemplate, EmailSignature

User = get_user_model()


class GmailService:
    """Gmail API service for sending and managing emails"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self, user):
        self.user = user
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Gmail API service with user credentials"""
        try:
            credentials = self._get_user_credentials()
            if credentials and credentials.valid:
                self.service = build('gmail', 'v1', credentials=credentials)
            elif credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self._save_user_credentials(credentials)
                self.service = build('gmail', 'v1', credentials=credentials)
        except Exception as e:
            print(f"Error initializing Gmail service: {e}")
            self.service = None
    
    def _get_user_credentials(self) -> Optional[Credentials]:
        """Get stored credentials for the user"""
        try:
            # Look for stored credentials in user profile or GoogleToken model
            from mobilize.authentication.models import GoogleToken
            token = GoogleToken.objects.filter(user=self.user).first()
            if token and token.access_token:
                # Convert stored scopes from string to list if needed
                if token.scopes:
                    if isinstance(token.scopes, str):
                        stored_scopes = token.scopes.split()
                    else:
                        stored_scopes = token.scopes
                else:
                    stored_scopes = self.SCOPES
                    
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
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """Get Gmail authorization URL for OAuth flow"""
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
        """Check if user has valid Gmail credentials"""
        return self.service is not None
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   body: str, 
                   is_html: bool = True,
                   cc_emails: Optional[List[str]] = None,
                   bcc_emails: Optional[List[str]] = None,
                   attachments: Optional[List[Dict]] = None,
                   template_id: Optional[int] = None,
                   signature_id: Optional[int] = None,
                   related_person_id: Optional[int] = None,
                   related_church_id: Optional[int] = None) -> Dict[str, Any]:
        """Send an email via Gmail API"""
        
        if not self.service:
            return {'success': False, 'error': 'Gmail service not authenticated'}
        
        try:
            # Create message
            message = MIMEMultipart()
            message['To'] = ', '.join(to_emails)
            message['Subject'] = subject
            message['From'] = self.user.email
            
            if cc_emails:
                message['Cc'] = ', '.join(cc_emails)
            if bcc_emails:
                message['Bcc'] = ', '.join(bcc_emails)
            
            # Add signature if specified
            email_body = body
            if signature_id:
                try:
                    signature = EmailSignature.objects.get(id=signature_id, user=self.user)
                    if is_html:
                        # Always convert line breaks to <br> for HTML emails
                        signature_html = signature.content.replace('\n', '<br>')
                        email_body += f"<br><br>{signature_html}"
                        
                        # Add company logo at the bottom of all HTML signatures
                        company_logo_url = "https://drive.google.com/uc?export=view&id=1s2fLid4Q686r1bGzb6JA84eC2E6N9zj2"
                        email_body += f'<br><br><img src="{company_logo_url}" alt="Crossover Global Logo" style="max-width: 200px; height: auto;">'
                    else:
                        email_body += f"\n\n{signature.content}"
                        # For plain text, just add a note about the logo
                        email_body += f"\n\n[Company Logo]"
                except EmailSignature.DoesNotExist:
                    pass
            
            # Add body
            if is_html:
                message.attach(MIMEText(email_body, 'html'))
            else:
                message.attach(MIMEText(email_body, 'plain'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    with open(attachment['path'], 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        message.attach(part)
            
            # Send message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw_message}
            
            result = self.service.users().messages().send(
                userId='me', 
                body=send_message
            ).execute()
            
            # Create communication record
            self._create_communication_record(
                to_emails=to_emails,
                cc_emails=cc_emails or [],
                bcc_emails=bcc_emails or [],
                subject=subject,
                body=body,
                gmail_message_id=result.get('id'),
                template_id=template_id,
                related_person_id=related_person_id,
                related_church_id=related_church_id
            )
            
            return {
                'success': True, 
                'message_id': result.get('id'),
                'thread_id': result.get('threadId')
            }
            
        except HttpError as error:
            return {'success': False, 'error': f'Gmail API error: {error}'}
        except Exception as error:
            return {'success': False, 'error': f'Unexpected error: {error}'}
    
    def _create_communication_record(self, **kwargs):
        """Create a communication record for sent email"""
        try:
            from mobilize.contacts.models import Person
            from mobilize.churches.models import Church
            
            person = None
            church = None
            
            if kwargs.get('related_person_id'):
                try:
                    person = Person.objects.get(contact_id=kwargs['related_person_id'])
                except Person.DoesNotExist:
                    pass
            
            if kwargs.get('related_church_id'):
                try:
                    church = Church.objects.get(id=kwargs['related_church_id'])
                except Church.DoesNotExist:
                    pass
            
            Communication.objects.create(
                type='email',
                subject=kwargs['subject'],
                message=kwargs['body'],
                direction='outbound',
                date=timezone.now().date(),
                date_sent=timezone.now(),
                person=person,
                church=church,
                gmail_message_id=kwargs.get('gmail_message_id'),
                email_status='sent',
                sender=self.user.email,
                user=self.user
            )
        except Exception as e:
            print(f"Error creating communication record: {e}")
    
    def get_messages(self, query: str = '', max_results: int = 10) -> List[Dict]:
        """Get Gmail messages matching query"""
        if not self.service:
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            detailed_messages = []
            
            for message in messages:
                msg_detail = self.service.users().messages().get(
                    userId='me', 
                    id=message['id']
                ).execute()
                detailed_messages.append(self._parse_message(msg_detail))
            
            return detailed_messages
            
        except HttpError as error:
            print(f'Gmail API error: {error}')
            return []
    
    def _parse_message(self, message: Dict) -> Dict:
        """Parse Gmail message into readable format"""
        headers = message['payload'].get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        to = next((h['value'] for h in headers if h['name'] == 'To'), '')
        
        # Extract body
        body = self._get_message_body(message['payload'])
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'to': to,
            'body': body,
            'snippet': message.get('snippet', '')
        }
    
    def _get_message_body(self, payload: Dict) -> str:
        """Extract message body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['body'].get('data'):
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
        
        return body
    
    def sync_emails_to_communications(self, days_back: int = 7, contacts_only: bool = True):
        """Sync recent Gmail messages to communications table"""
        if not self.service:
            return {'success': False, 'error': 'Gmail service not authenticated'}
        
        from datetime import datetime, timedelta
        
        # Get all known contact emails if we're filtering by contacts only
        if contacts_only:
            known_emails = set()
            try:
                from mobilize.contacts.models import Person
                from mobilize.churches.models import Church
                
                # Get all person emails
                person_emails = Person.objects.filter(
                    contact__email__isnull=False
                ).exclude(contact__email='').values_list('contact__email', flat=True)
                known_emails.update(person_emails)
                
                # Get all church emails
                church_emails = Church.objects.filter(
                    contact__email__isnull=False
                ).exclude(contact__email='').values_list('contact__email', flat=True)
                known_emails.update(church_emails)
                
                print(f"Found {len(known_emails)} known contact emails")
            except Exception as e:
                print(f"Error getting known emails: {e}")
                known_emails = set()
        
        # Query for recent emails
        since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        query = f'after:{since_date}'
        
        messages = self.get_messages(query=query, max_results=500)  # Increased limit
        synced_count = 0
        skipped_count = 0
        
        for message in messages:
            # Check if communication already exists
            if Communication.objects.filter(gmail_message_id=message['id']).exists():
                continue
                
            # If contacts_only is True, skip emails not from known contacts
            if contacts_only and message.get('sender'):
                sender_email = message['sender'].lower().strip()
                if sender_email not in known_emails:
                    skipped_count += 1
                    continue
            
            # Try to match to contacts by email
            person = self._find_person_by_email(message['sender'])
            church = self._find_church_by_email(message['sender'])
            
            # Only create if we found a matching contact (when contacts_only=True)
            if contacts_only and not person and not church:
                skipped_count += 1
                continue
            
            # Handle the person ID mapping correctly
            person_id = None
            if person:
                # Get the actual person.id from the database (not contact_id)
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute('SELECT id FROM people WHERE contact_id = %s', [person.pk])
                    result = cursor.fetchone()
                    if result:
                        person_id = result[0]
            
            Communication.objects.create(
                type='email',
                subject=message['subject'],
                message=message['body'][:250],  # Truncate for database field
                direction='inbound',
                date=timezone.now().date(),
                person_id=person_id,  # Use person_id instead of person object
                church=church,
                gmail_message_id=message['id'],
                gmail_thread_id=message['thread_id'],
                email_status='received',
                sender=message['sender'],
                user=self.user
            )
            synced_count += 1
        
        result = {'success': True, 'synced_count': synced_count}
        if contacts_only:
            result['skipped_count'] = skipped_count
            result['message'] = f'Synced {synced_count} emails from known contacts, skipped {skipped_count} emails from unknown contacts'
        
        return result
    
    def _find_person_by_email(self, email_address: str):
        """Find person by email address"""
        try:
            from mobilize.contacts.models import Person
            return Person.objects.filter(contact__email=email_address).first()
        except:
            return None
    
    def _find_church_by_email(self, email_address: str):
        """Find church by email address"""
        try:
            from mobilize.churches.models import Church
            return Church.objects.filter(contact__email=email_address).first()
        except:
            return None