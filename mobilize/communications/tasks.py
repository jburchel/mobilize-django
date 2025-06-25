"""
Celery tasks for communications processing.

This module contains background tasks for processing emails,
managing communication queues, and handling email-related operations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Communication, EmailTemplate, EmailSignature
from .gmail_service import GmailService
from mobilize.contacts.models import Contact

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_pending_emails(self):
    """
    Process all pending email communications in the queue.
    
    This task runs periodically to send emails that are queued
    for delivery but haven't been sent yet.
    """
    try:
        # Get all pending communications
        pending_communications = Communication.objects.filter(
            type='email',
            status='pending'
        ).select_related('user', 'person')
        
        processed_count = 0
        failed_count = 0
        
        for communication in pending_communications:
            try:
                # Send the email
                result = send_email_communication.delay(communication.id)
                processed_count += 1
                logger.info(f"Queued email communication {communication.id} for sending")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to queue email communication {communication.id}: {str(e)}")
        
        logger.info(f"Processed {processed_count} emails, {failed_count} failed")
        return {
            'processed': processed_count,
            'failed': failed_count,
            'total': pending_communications.count()
        }
        
    except Exception as exc:
        logger.error(f"Error processing pending emails: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_communication(self, communication_id: int):
    """
    Send a specific email communication.
    
    Args:
        communication_id: ID of the Communication record to send
    """
    try:
        communication = Communication.objects.select_related(
            'user', 'person', 'person__contact'
        ).get(id=communication_id)
        
        if communication.status != 'pending':
            logger.warning(f"Communication {communication_id} is not pending, skipping")
            return {'status': 'skipped', 'reason': 'not_pending'}
        
        # Mark as processing
        communication.status = 'processing'
        communication.save()
        
        # Get user's Gmail service
        gmail_service = GmailService(communication.user)
        
        # Prepare email data
        to_email = communication.person.contact.email
        if not to_email:
            raise ValueError(f"No email address for contact {communication.person.contact.id}")
        
        # Get email signature if available
        signature = ""
        try:
            email_signature = EmailSignature.objects.get(user=communication.user, is_default=True)
            signature = email_signature.get_signature_html()
        except EmailSignature.DoesNotExist:
            pass
        
        # Append signature to content if available
        content = communication.content
        if signature:
            content += f"\n\n{signature}"
        
        # Send email via Gmail API
        message = gmail_service.send_email(
            to=to_email,
            subject=communication.subject or "Message from Mobilize CRM",
            body=content,
            cc=communication.cc_recipients.split(',') if communication.cc_recipients else None,
            bcc=communication.bcc_recipients.split(',') if communication.bcc_recipients else None,
        )
        
        # Update communication record
        with transaction.atomic():
            communication.status = 'sent'
            communication.date_sent = timezone.now()
            communication.external_id = message.get('id', '')
            communication.save()
        
        logger.info(f"Successfully sent email communication {communication_id}")
        return {
            'status': 'sent',
            'communication_id': communication_id,
            'message_id': message.get('id', '')
        }
        
    except Communication.DoesNotExist:
        logger.error(f"Communication {communication_id} not found")
        return {'status': 'error', 'reason': 'not_found'}
        
    except Exception as exc:
        # Mark communication as failed
        try:
            communication = Communication.objects.get(id=communication_id)
            communication.status = 'failed'
            communication.error_message = str(exc)
            communication.save()
        except:
            pass
        
        logger.error(f"Failed to send email communication {communication_id}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_gmail_emails(self, user_id: int, days_back: int = 7):
    """
    Sync emails from Gmail for a specific user.
    
    Args:
        user_id: ID of the user to sync emails for
        days_back: Number of days back to sync emails
    """
    try:
        user = User.objects.get(id=user_id)
        gmail_service = GmailService(user)
        
        # Calculate date range
        since_date = timezone.now() - timedelta(days=days_back)
        
        # Get emails from Gmail
        emails = gmail_service.get_emails(since_date=since_date)
        
        synced_count = 0
        for email_data in emails:
            try:
                # Extract email information
                sender_email = email_data.get('sender_email', '')
                recipient_emails = email_data.get('recipient_emails', [])
                
                # Find related contacts
                related_contacts = Contact.objects.filter(
                    email__in=[sender_email] + recipient_emails
                ).first()
                
                if related_contacts:
                    # Create communication record
                    communication, created = Communication.objects.get_or_create(
                        external_id=email_data.get('id', ''),
                        defaults={
                            'user': user,
                            'person': getattr(related_contacts, 'person', None),
                            'type': 'email',
                            'subject': email_data.get('subject', ''),
                            'content': email_data.get('body', ''),
                            'status': 'sent',
                            'date_sent': email_data.get('date', timezone.now()),
                            'created_at': timezone.now(),
                        }
                    )
                    
                    if created:
                        synced_count += 1
                        
            except Exception as e:
                logger.error(f"Error syncing email {email_data.get('id', '')}: {str(e)}")
        
        logger.info(f"Synced {synced_count} emails for user {user_id}")
        return {
            'user_id': user_id,
            'synced_count': synced_count,
            'total_emails': len(emails)
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'error', 'reason': 'user_not_found'}
        
    except Exception as exc:
        logger.error(f"Error syncing Gmail emails for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def send_bulk_email(self, template_id: int, contact_ids: List[int], user_id: int, subject_override: str = None):
    """
    Send bulk emails using an email template to multiple contacts.
    
    Args:
        template_id: ID of the EmailTemplate to use
        contact_ids: List of Contact IDs to send to
        user_id: ID of the user sending the emails
        subject_override: Optional subject override
    """
    try:
        user = User.objects.get(id=user_id)
        template = EmailTemplate.objects.get(id=template_id)
        contacts = Contact.objects.filter(id__in=contact_ids, email__isnull=False)
        
        sent_count = 0
        failed_count = 0
        
        for contact in contacts:
            try:
                # Create communication record
                communication = Communication.objects.create(
                    user=user,
                    person=getattr(contact, 'person', None),
                    type='email',
                    subject=subject_override or template.subject,
                    content=template.body,
                    status='pending',
                    template_used=template,
                )
                
                # Queue for sending
                send_email_communication.delay(communication.id)
                sent_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to create communication for contact {contact.id}: {str(e)}")
        
        logger.info(f"Bulk email job completed: {sent_count} queued, {failed_count} failed")
        return {
            'template_id': template_id,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_contacts': len(contact_ids)
        }
        
    except (User.DoesNotExist, EmailTemplate.DoesNotExist) as e:
        logger.error(f"Bulk email error: {str(e)}")
        return {'status': 'error', 'reason': str(e)}
        
    except Exception as exc:
        logger.error(f"Error sending bulk email: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def cleanup_old_communications(self, days_to_keep: int = 90):
    """
    Clean up old communication records to manage database size.
    
    Args:
        days_to_keep: Number of days of communications to keep
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Delete old communications (keep failed ones for debugging)
        deleted_count = Communication.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['sent', 'delivered']
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old communication records")
        return {'deleted_count': deleted_count, 'cutoff_date': cutoff_date.isoformat()}
        
    except Exception as exc:
        logger.error(f"Error cleaning up communications: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def process_email_bounces(self, user_id: int):
    """
    Process email bounces and update contact status accordingly.
    
    Args:
        user_id: ID of the user to process bounces for
    """
    try:
        user = User.objects.get(id=user_id)
        gmail_service = GmailService(user)
        
        # This would integrate with Gmail's bounce detection
        # For now, this is a placeholder for future implementation
        
        logger.info(f"Processed email bounces for user {user_id}")
        return {'user_id': user_id, 'status': 'completed'}
        
    except Exception as exc:
        logger.error(f"Error processing email bounces: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def generate_email_analytics(self, user_id: int, date_range_days: int = 30):
    """
    Generate email analytics for dashboard display.
    
    Args:
        user_id: ID of the user to generate analytics for
        date_range_days: Number of days to include in analytics
    """
    try:
        user = User.objects.get(id=user_id)
        start_date = timezone.now() - timedelta(days=date_range_days)
        
        # Calculate email statistics
        communications = Communication.objects.filter(
            user=user,
            type='email',
            created_at__gte=start_date
        )
        
        analytics = {
            'total_sent': communications.filter(status='sent').count(),
            'total_failed': communications.filter(status='failed').count(),
            'total_pending': communications.filter(status='pending').count(),
            'date_range_days': date_range_days,
            'generated_at': timezone.now().isoformat(),
        }
        
        # Store analytics in cache for dashboard
        from django.core.cache import cache
        cache.set(f'email_analytics_{user_id}', analytics, timeout=3600)  # Cache for 1 hour
        
        logger.info(f"Generated email analytics for user {user_id}")
        return analytics
        
    except Exception as exc:
        logger.error(f"Error generating email analytics: {str(exc)}")
        raise self.retry(exc=exc)