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
        
        if not gmail_service.is_authenticated():
            logger.warning(f"User {user_id} Gmail not authenticated, skipping sync")
            return {'status': 'skipped', 'reason': 'not_authenticated'}
        
        # Use the actual Gmail service sync method
        result = gmail_service.sync_emails_to_communications(days_back, contacts_only=True)
        
        if result['success']:
            logger.info(f"Synced {result['synced_count']} emails for user {user_id}")
            return {
                'user_id': user_id,
                'synced_count': result['synced_count'],
                'skipped_count': result.get('skipped_count', 0),
                'status': 'success'
            }
        else:
            logger.error(f"Gmail sync failed for user {user_id}: {result['error']}")
            return {'status': 'error', 'reason': result['error']}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'error', 'reason': 'user_not_found'}
        
    except Exception as exc:
        logger.error(f"Error syncing Gmail emails for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def sync_all_users_gmail(self, days_back: int = 1):
    """
    Sync Gmail emails for all authenticated users and send notifications for new emails.
    
    Args:
        days_back: Number of days back to sync emails (default: 1 for frequent syncing)
    """
    try:
        # Get all users who have Gmail tokens
        from mobilize.authentication.models import GoogleToken
        
        authenticated_users = User.objects.filter(
            id__in=GoogleToken.objects.filter(
                access_token__isnull=False
            ).values_list('user_id', flat=True),
            is_active=True
        )
        
        total_synced = 0
        users_processed = 0
        users_with_new_emails = []
        
        for user in authenticated_users:
            try:
                result = sync_gmail_emails.delay(user.id, days_back).get()
                
                if result.get('status') == 'success':
                    synced_count = result.get('synced_count', 0)
                    total_synced += synced_count
                    users_processed += 1
                    
                    # If user has new emails, add to notification list
                    if synced_count > 0:
                        users_with_new_emails.append({
                            'user': user,
                            'new_emails': synced_count,
                            'skipped_count': result.get('skipped_count', 0)
                        })
                        
                elif result.get('status') == 'skipped':
                    logger.info(f"Skipped user {user.username} - {result.get('reason')}")
                else:
                    logger.warning(f"Gmail sync failed for user {user.username}: {result.get('reason')}")
                    
            except Exception as e:
                logger.error(f"Error syncing Gmail for user {user.username}: {str(e)}")
        
        # Send notifications for users with new emails
        if users_with_new_emails:
            send_new_email_notifications.delay(users_with_new_emails)
        
        logger.info(f"Gmail auto-sync completed: {total_synced} emails synced for {users_processed} users")
        return {
            'total_synced': total_synced,
            'users_processed': users_processed,
            'users_with_new_emails': len(users_with_new_emails),
            'status': 'completed'
        }
        
    except Exception as exc:
        logger.error(f"Error in auto Gmail sync: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def send_new_email_notifications(self, users_with_new_emails: List[Dict]):
    """
    Send notifications to users who received new emails.
    
    Args:
        users_with_new_emails: List of dictionaries with user info and email counts
    """
    try:
        from django.contrib.messages import get_messages
        from django.contrib.messages.storage.fallback import FallbackStorage
        
        notifications_sent = 0
        
        for user_data in users_with_new_emails:
            try:
                user = user_data['user']
                new_email_count = user_data['new_emails']
                skipped_count = user_data.get('skipped_count', 0)
                
                # Create a notification message
                if new_email_count == 1:
                    message = f"📧 You have 1 new email from a contact in your CRM."
                else:
                    message = f"📧 You have {new_email_count} new emails from contacts in your CRM."
                
                if skipped_count > 0:
                    message += f" ({skipped_count} emails from unknown contacts were skipped.)"
                
                # Log the notification (in a real app, you might use Django's messaging framework,
                # push notifications, or email notifications)
                logger.info(f"📧 NEW EMAIL NOTIFICATION for {user.username}: {message}")
                
                # Here you could:
                # 1. Create a Notification model record
                # 2. Send a push notification
                # 3. Add to user's session messages for next login
                # 4. Send an email notification
                # 5. Use WebSocket for real-time notification
                
                # For now, we'll create a simple log entry that could be displayed in the UI
                from django.core.cache import cache
                notification_key = f"gmail_notification_{user.id}"
                cache.set(notification_key, {
                    'message': message,
                    'timestamp': timezone.now().isoformat(),
                    'new_emails': new_email_count,
                    'read': False
                }, timeout=86400)  # Cache for 24 hours
                
                notifications_sent += 1
                
            except Exception as e:
                logger.error(f"Error sending notification: {str(e)}")
        
        logger.info(f"Sent {notifications_sent} new email notifications")
        return {
            'notifications_sent': notifications_sent,
            'total_users': len(users_with_new_emails)
        }
        
    except Exception as exc:
        logger.error(f"Error sending new email notifications: {str(exc)}")
        return {'status': 'error', 'reason': str(exc)}


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