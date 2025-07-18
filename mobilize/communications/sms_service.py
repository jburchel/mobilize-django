"""
SMS Service for Twilio Integration
Handles SMS sending, receiving, and logging functionality
"""

import logging
import re
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from .models import Communication
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.contacts.models import Contact

logger = logging.getLogger(__name__)


class SMSService:
    """Service class for handling SMS operations via Twilio"""
    
    def __init__(self):
        """Initialize the SMS service with Twilio client"""
        self.client = None
        self.from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
        
        # Initialize Twilio client
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        
        if account_sid and auth_token:
            try:
                self.client = Client(account_sid, auth_token)
                logger.info("Twilio SMS service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None
        else:
            logger.warning("Twilio credentials not found in settings")
    
    def is_enabled(self):
        """Check if SMS service is properly configured"""
        return self.client is not None and self.from_number is not None
    
    def normalize_phone_number(self, phone_number):
        """Normalize phone number to E.164 format"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_number)
        
        # If it's a US number (10 digits), add +1
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        elif digits.startswith('+'):
            return digits
        else:
            # Assume it's already in correct format or international
            return f"+{digits}"
    
    def send_sms(self, to_number, message_body, user=None, contact=None):
        """
        Send SMS message and log the communication
        
        Args:
            to_number (str): Recipient phone number
            message_body (str): SMS message content
            user: User sending the message
            contact: Contact object (Person or Church)
        
        Returns:
            dict: Result with success status and message/error
        """
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'SMS service not configured. Please check Twilio settings.'
            }
        
        try:
            # Normalize phone numbers
            to_number = self.normalize_phone_number(to_number)
            
            # Send SMS via Twilio
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )
            
            # Log the communication
            self._log_sms_communication(
                phone_number=to_number,
                message_body=message_body,
                message_sid=message.sid,
                direction='outbound',
                user=user,
                contact=contact
            )
            
            logger.info(f"SMS sent successfully to {to_number}, SID: {message.sid}")
            
            return {
                'success': True,
                'message_sid': message.sid,
                'message': 'SMS sent successfully'
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS to {to_number}: {e}")
            return {
                'success': False,
                'error': f'Failed to send SMS: {e.msg}'
            }
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {to_number}: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred while sending SMS'
            }
    
    def handle_incoming_sms(self, from_number, body, message_sid):
        """
        Handle incoming SMS webhook from Twilio
        
        Args:
            from_number (str): Sender phone number
            body (str): SMS message content
            message_sid (str): Twilio message SID
        
        Returns:
            dict: Processing result
        """
        try:
            # Normalize phone number
            from_number = self.normalize_phone_number(from_number)
            
            # Try to find contact by phone number
            contact = self._find_contact_by_phone(from_number)
            
            # Log the incoming SMS
            self._log_sms_communication(
                phone_number=from_number,
                message_body=body,
                message_sid=message_sid,
                direction='inbound',
                contact=contact
            )
            
            logger.info(f"Incoming SMS logged from {from_number}, SID: {message_sid}")
            
            return {
                'success': True,
                'contact_found': contact is not None,
                'contact': contact
            }
            
        except Exception as e:
            logger.error(f"Error handling incoming SMS from {from_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_contact_by_phone(self, phone_number):
        """Find contact (Person or Church) by phone number"""
        try:
            # Search for contact by phone number
            # Try exact match first
            contact = Contact.objects.filter(phone=phone_number).first()
            
            if not contact:
                # Try without country code if US number
                if phone_number.startswith('+1'):
                    search_number = phone_number[2:]  # Remove +1
                    contact = Contact.objects.filter(phone=search_number).first()
                
                if not contact:
                    # Try with various formatting
                    digits = re.sub(r'\D', '', phone_number)
                    if len(digits) >= 10:
                        last_10 = digits[-10:]  # Get last 10 digits
                        contact = Contact.objects.filter(
                            phone__icontains=last_10
                        ).first()
            
            return contact
            
        except Exception as e:
            logger.error(f"Error finding contact by phone {phone_number}: {e}")
            return None
    
    def _log_sms_communication(self, phone_number, message_body, message_sid, 
                             direction, user=None, contact=None):
        """Log SMS communication to database"""
        try:
            # Determine person and church from contact
            person = None
            church = None
            
            if contact:
                if hasattr(contact, 'person_details'):
                    person = contact.person_details
                elif hasattr(contact, 'church_details'):
                    church = contact.church_details
            
            # Create communication record
            communication = Communication.objects.create(
                type='Text Message',
                direction=direction,
                message=message_body,
                subject=f"SMS {'to' if direction == 'outbound' else 'from'} {phone_number}",
                date=timezone.now().date(),
                date_sent=timezone.now(),
                person=person,
                church=church,
                user=user,
                office=user.office if user else None,
                gmail_message_id=message_sid,  # Store Twilio SID here
                email_status='sent' if direction == 'outbound' else 'received'
            )
            
            logger.info(f"SMS communication logged: {communication.id}")
            return communication
            
        except Exception as e:
            logger.error(f"Error logging SMS communication: {e}")
            return None
    
    def get_message_status(self, message_sid):
        """Get message status from Twilio"""
        if not self.is_enabled():
            return None
        
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
        except Exception as e:
            logger.error(f"Error fetching message status for {message_sid}: {e}")
            return None


# Global instance
sms_service = SMSService()