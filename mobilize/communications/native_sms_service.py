"""
Native SMS Logging Service
Handles incoming SMS logging without external services
"""

import logging
import re
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Communication
from mobilize.contacts.models import Person, Contact
from mobilize.churches.models import Church

logger = logging.getLogger(__name__)
User = get_user_model()


class NativeSMSService:
    """Service class for handling native SMS logging"""

    def __init__(self):
        """Initialize the native SMS service"""
        self.enabled = True
        logger.info("Native SMS logging service initialized")

    def normalize_phone_number(self, phone_number):
        """Normalize phone number to E.164 format"""
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", phone_number)

        # If it's a US number (10 digits), add +1
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
        elif phone_number.startswith("+"):
            return phone_number
        else:
            # Assume it's already in correct format or international
            return f"+{digits}" if digits else phone_number

    def log_incoming_sms(self, from_number, message_body, user=None, timestamp=None):
        """
        Log incoming SMS message manually
        
        Args:
            from_number (str): Sender phone number
            message_body (str): SMS message content
            user: User who is logging this SMS (optional)
            timestamp: When the SMS was received (optional, defaults to now)
            
        Returns:
            dict: Result with success status and communication object
        """
        try:
            # Normalize phone number
            normalized_number = self.normalize_phone_number(from_number)
            
            # Try to find contact by phone number
            contact = self._find_contact_by_phone(normalized_number)
            
            # Use current timestamp if not provided
            if timestamp is None:
                timestamp = timezone.now()
            
            # Create communication record
            communication = self._create_sms_communication(
                phone_number=normalized_number,
                original_phone=from_number,
                message_body=message_body,
                contact=contact,
                user=user,
                timestamp=timestamp,
                direction="inbound"
            )
            
            logger.info(f"Incoming SMS logged from {normalized_number}, Communication ID: {communication.id}")
            
            return {
                "success": True,
                "communication": communication,
                "contact_found": contact is not None,
                "contact": contact,
                "contact_name": self._get_contact_name(contact) if contact else None,
                "normalized_phone": normalized_number
            }
            
        except Exception as e:
            logger.error(f"Error logging incoming SMS from {from_number}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def log_outgoing_sms(self, to_number, message_body, user=None, timestamp=None):
        """
        Log outgoing SMS message manually
        
        Args:
            to_number (str): Recipient phone number
            message_body (str): SMS message content
            user: User who sent this SMS (optional)
            timestamp: When the SMS was sent (optional, defaults to now)
            
        Returns:
            dict: Result with success status and communication object
        """
        try:
            # Normalize phone number
            normalized_number = self.normalize_phone_number(to_number)
            
            # Try to find contact by phone number
            contact = self._find_contact_by_phone(normalized_number)
            
            # Use current timestamp if not provided
            if timestamp is None:
                timestamp = timezone.now()
            
            # Create communication record
            communication = self._create_sms_communication(
                phone_number=normalized_number,
                original_phone=to_number,
                message_body=message_body,
                contact=contact,
                user=user,
                timestamp=timestamp,
                direction="outbound"
            )
            
            logger.info(f"Outgoing SMS logged to {normalized_number}, Communication ID: {communication.id}")
            
            return {
                "success": True,
                "communication": communication,
                "contact_found": contact is not None,
                "contact": contact,
                "contact_name": self._get_contact_name(contact) if contact else None,
                "normalized_phone": normalized_number
            }
            
        except Exception as e:
            logger.error(f"Error logging outgoing SMS to {to_number}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _find_contact_by_phone(self, phone_number):
        """Find contact (Person or Church) by phone number"""
        try:
            # Search for contact by phone number
            # Try exact match first
            contact = Contact.objects.filter(phone=phone_number).first()

            if not contact:
                # Try without country code if US number
                if phone_number.startswith("+1"):
                    search_number = phone_number[2:]  # Remove +1
                    contact = Contact.objects.filter(phone=search_number).first()

                if not contact:
                    # Try with various formatting
                    digits = re.sub(r"\D", "", phone_number)
                    if len(digits) >= 10:
                        last_10 = digits[-10:]  # Get last 10 digits
                        contact = Contact.objects.filter(
                            phone__icontains=last_10
                        ).first()
                        
                        if not contact:
                            # Try with different formatting patterns
                            formatted_patterns = [
                                f"({last_10[:3]}) {last_10[3:6]}-{last_10[6:]}",  # (123) 456-7890
                                f"{last_10[:3]}-{last_10[3:6]}-{last_10[6:]}",    # 123-456-7890
                                f"{last_10[:3]}.{last_10[3:6]}.{last_10[6:]}",    # 123.456.7890
                                last_10,  # 1234567890
                            ]
                            
                            for pattern in formatted_patterns:
                                contact = Contact.objects.filter(phone__exact=pattern).first()
                                if contact:
                                    break

            return contact

        except Exception as e:
            logger.error(f"Error finding contact by phone {phone_number}: {e}")
            return None

    def _get_contact_name(self, contact):
        """Get display name for contact"""
        if not contact:
            return None
            
        try:
            if hasattr(contact, 'person_details') and contact.person_details:
                person = contact.person_details
                return f"{person.first_name} {person.last_name}".strip()
            elif hasattr(contact, 'church_details') and contact.church_details:
                church = contact.church_details
                return church.name
            else:
                # Try to get name from contact directly
                return getattr(contact, 'name', 'Unknown Contact')
        except Exception as e:
            logger.error(f"Error getting contact name: {e}")
            return 'Unknown Contact'

    def _create_sms_communication(self, phone_number, original_phone, message_body, contact, user, timestamp, direction):
        """Create SMS communication record in database"""
        try:
            # Determine person and church from contact
            person = None
            church = None
            contact_name = "Unknown Contact"

            if contact:
                contact_name = self._get_contact_name(contact)
                if hasattr(contact, "person_details") and contact.person_details:
                    person = contact.person_details
                elif hasattr(contact, "church_details") and contact.church_details:
                    church = contact.church_details

            # Create subject line
            direction_text = "from" if direction == "inbound" else "to"
            subject = f"SMS {direction_text} {contact_name if contact else original_phone}"

            # Create communication record
            communication = Communication.objects.create(
                type="Text Message",
                direction=direction,
                message=message_body,
                content=message_body,  # Also store in content field
                subject=subject,
                date=timestamp.date(),
                date_sent=timestamp,
                person=person,
                church=church,
                user=user,
                office=user.office if user else None,
                sender=phone_number if direction == "inbound" else None,
                status="received" if direction == "inbound" else "sent",
                external_id=f"native_sms_{timestamp.timestamp()}",  # Unique identifier
            )

            logger.info(f"SMS communication created: {communication.id}")
            return communication

        except Exception as e:
            logger.error(f"Error creating SMS communication: {e}")
            raise

    def get_recent_sms_for_contact(self, contact, limit=10):
        """Get recent SMS communications for a contact"""
        try:
            person = None
            church = None
            
            if hasattr(contact, "person_details") and contact.person_details:
                person = contact.person_details
            elif hasattr(contact, "church_details") and contact.church_details:
                church = contact.church_details
            
            # Build query
            query = Communication.objects.filter(type="Text Message")
            
            if person:
                query = query.filter(person=person)
            elif church:
                query = query.filter(church=church)
            else:
                return []
            
            return query.order_by('-date_sent')[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent SMS for contact: {e}")
            return []

    def get_sms_statistics(self, user=None, office=None):
        """Get SMS statistics for dashboard"""
        try:
            query = Communication.objects.filter(type="Text Message")
            
            if user:
                query = query.filter(user=user)
            elif office:
                query = query.filter(office=office)
            
            total_sms = query.count()
            inbound_sms = query.filter(direction="inbound").count()
            outbound_sms = query.filter(direction="outbound").count()
            
            # Get recent SMS count (last 7 days)
            week_ago = timezone.now() - timezone.timedelta(days=7)
            recent_sms = query.filter(date_sent__gte=week_ago).count()
            
            return {
                "total_sms": total_sms,
                "inbound_sms": inbound_sms,
                "outbound_sms": outbound_sms,
                "recent_sms": recent_sms,
            }
            
        except Exception as e:
            logger.error(f"Error getting SMS statistics: {e}")
            return {
                "total_sms": 0,
                "inbound_sms": 0,
                "outbound_sms": 0,
                "recent_sms": 0,
            }


# Global instance
native_sms_service = NativeSMSService()