"""
Celery tasks for task management and notifications.

This module contains background tasks for processing task notifications,
managing recurring tasks, and handling task-related operations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Task, RecurringTaskTemplate
from mobilize.communications.models import Communication
from mobilize.contacts.models import Contact

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_due_date_notifications(self):
    """
    Send notifications for tasks that are due soon or overdue.

    This task runs periodically to notify users about upcoming
    and overdue tasks.
    """
    try:
        now = timezone.now()

        # Get tasks due in the next 24 hours
        upcoming_tasks = Task.objects.filter(
            due_date__gte=now,
            due_date__lte=now + timedelta(hours=24),
            status__in=["pending", "in_progress"],
            notification_sent=False,
        ).select_related("assigned_to", "contact", "created_by")

        # Get overdue tasks
        overdue_tasks = Task.objects.filter(
            due_date__lt=now,
            status__in=["pending", "in_progress"],
            overdue_notification_sent=False,
        ).select_related("assigned_to", "contact", "created_by")

        notifications_sent = 0

        # Process upcoming tasks
        for task in upcoming_tasks:
            try:
                send_task_notification.delay(task.id, "upcoming")
                task.notification_sent = True
                task.save()
                notifications_sent += 1

            except Exception as e:
                logger.error(
                    f"Failed to send upcoming notification for task {task.id}: {str(e)}"
                )

        # Process overdue tasks
        for task in overdue_tasks:
            try:
                send_task_notification.delay(task.id, "overdue")
                task.overdue_notification_sent = True
                task.save()
                notifications_sent += 1

            except Exception as e:
                logger.error(
                    f"Failed to send overdue notification for task {task.id}: {str(e)}"
                )

        logger.info(f"Sent {notifications_sent} task notifications")
        return {
            "notifications_sent": notifications_sent,
            "upcoming_count": upcoming_tasks.count(),
            "overdue_count": overdue_tasks.count(),
        }

    except Exception as exc:
        logger.error(f"Error sending due date notifications: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_notification(self, task_id: int, notification_type: str):
    """
    Send a specific task notification.

    Args:
        task_id: ID of the Task to send notification for
        notification_type: Type of notification ('upcoming', 'overdue', 'assigned')
    """
    try:
        task = Task.objects.select_related("assigned_to", "contact", "created_by").get(
            id=task_id
        )

        if not task.assigned_to or not task.assigned_to.email:
            logger.warning(f"No email address for task {task_id} assignee")
            return {"status": "skipped", "reason": "no_email"}

        # Prepare notification content based on type
        context = {
            "task": task,
            "user": task.assigned_to,
            "notification_type": notification_type,
            "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
        }

        if notification_type == "upcoming":
            subject = f"Task Due Soon: {task.title}"
            template = "tasks/emails/task_due_soon.html"
        elif notification_type == "overdue":
            subject = f"Overdue Task: {task.title}"
            template = "tasks/emails/task_overdue.html"
        elif notification_type == "assigned":
            subject = f"New Task Assigned: {task.title}"
            template = "tasks/emails/task_assigned.html"
        else:
            raise ValueError(f"Unknown notification type: {notification_type}")

        # Render email content
        try:
            email_content = render_to_string(template, context)
        except Exception:
            # Fallback to simple text email if template doesn't exist
            email_content = f"""
            Task Notification: {subject}
            
            Task: {task.title}
            Description: {task.description or 'No description'}
            Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'Not set'}
            Priority: {task.get_priority_display()}
            
            View task: {context['site_url']}/tasks/{task.id}/
            """

        # Create communication record
        communication = Communication.objects.create(
            user=task.created_by or task.assigned_to,
            person=(
                getattr(task.contact, "person", None)
                if hasattr(task.contact, "person")
                else None
            ),
            type="email",
            subject=subject,
            content=email_content,
            status="pending",
            is_notification=True,
        )

        # Send via email processing task
        from mobilize.communications.tasks import send_email_communication

        send_email_communication.delay(communication.id)

        logger.info(f"Queued {notification_type} notification for task {task_id}")
        return {
            "status": "sent",
            "task_id": task_id,
            "notification_type": notification_type,
            "communication_id": communication.id,
        }

    except Task.DoesNotExist:
        logger.error(f"Task {task_id} not found")
        return {"status": "error", "reason": "task_not_found"}

    except Exception as exc:
        logger.error(f"Failed to send task notification {task_id}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_recurring_tasks(self):
    """
    Generate new tasks from recurring task templates.

    This task runs periodically to create new instances of recurring tasks
    based on their schedule.
    """
    try:
        now = timezone.now()
        templates = RecurringTaskTemplate.objects.filter(is_active=True)

        created_count = 0

        for template in templates:
            try:
                # Check if it's time to create a new task based on the template
                if template.should_create_new_task(now):
                    # Create new task from template
                    new_task = Task.objects.create(
                        title=template.title,
                        description=template.description,
                        assigned_to=template.default_assignee,
                        contact=template.default_contact,
                        priority=template.priority,
                        due_date=template.calculate_next_due_date(now),
                        status="pending",
                        created_by=template.created_by,
                        recurring_template=template,
                    )

                    # Update template's next creation date
                    template.last_created = now
                    template.save()

                    # Send assignment notification if needed
                    if template.send_notifications and new_task.assigned_to:
                        send_task_notification.delay(new_task.id, "assigned")

                    created_count += 1
                    logger.info(
                        f"Created recurring task {new_task.id} from template {template.id}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to create task from template {template.id}: {str(e)}"
                )

        logger.info(f"Generated {created_count} recurring tasks")
        return {
            "created_count": created_count,
            "templates_processed": templates.count(),
        }

    except Exception as exc:
        logger.error(f"Error generating recurring tasks: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def update_task_statistics(self, user_id: int = None):
    """
    Update task statistics for dashboard display.

    Args:
        user_id: Optional user ID to generate statistics for (all users if None)
    """
    try:
        from django.core.cache import cache

        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            users = User.objects.filter(is_active=True)

        for user in users:
            # Calculate task statistics
            user_tasks = Task.objects.filter(assigned_to=user)

            stats = {
                "total_tasks": user_tasks.count(),
                "pending_tasks": user_tasks.filter(status="pending").count(),
                "in_progress_tasks": user_tasks.filter(status="in_progress").count(),
                "completed_tasks": user_tasks.filter(status="completed").count(),
                "overdue_tasks": user_tasks.filter(
                    due_date__lt=timezone.now(), status__in=["pending", "in_progress"]
                ).count(),
                "due_today": user_tasks.filter(
                    due_date__date=timezone.now().date(),
                    status__in=["pending", "in_progress"],
                ).count(),
                "due_this_week": user_tasks.filter(
                    due_date__gte=timezone.now(),
                    due_date__lt=timezone.now() + timedelta(days=7),
                    status__in=["pending", "in_progress"],
                ).count(),
                "updated_at": timezone.now().isoformat(),
            }

            # Cache the statistics
            cache.set(f"task_stats_{user.id}", stats, timeout=3600)  # Cache for 1 hour

        logger.info(f"Updated task statistics for {users.count()} users")
        return {"users_processed": users.count()}

    except Exception as exc:
        logger.error(f"Error updating task statistics: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def cleanup_completed_tasks(self, days_to_keep: int = 365):
    """
    Clean up old completed tasks to manage database size.

    Args:
        days_to_keep: Number of days of completed tasks to keep
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Delete old completed tasks
        deleted_count = Task.objects.filter(
            status="completed", completed_at__lt=cutoff_date
        ).delete()[0]

        logger.info(f"Cleaned up {deleted_count} old completed tasks")
        return {"deleted_count": deleted_count, "cutoff_date": cutoff_date.isoformat()}

    except Exception as exc:
        logger.error(f"Error cleaning up completed tasks: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def send_daily_task_digest(self, user_id: int):
    """
    Send a daily digest of tasks to a user.

    Args:
        user_id: ID of the user to send digest to
    """
    try:
        user = User.objects.get(id=user_id)

        if not user.email:
            logger.warning(f"No email address for user {user_id}")
            return {"status": "skipped", "reason": "no_email"}

        now = timezone.now()
        today = now.date()

        # Get tasks for digest
        tasks_data = {
            "overdue": Task.objects.filter(
                assigned_to=user,
                due_date__lt=now,
                status__in=["pending", "in_progress"],
            ),
            "due_today": Task.objects.filter(
                assigned_to=user,
                due_date__date=today,
                status__in=["pending", "in_progress"],
            ),
            "due_tomorrow": Task.objects.filter(
                assigned_to=user,
                due_date__date=today + timedelta(days=1),
                status__in=["pending", "in_progress"],
            ),
            "completed_yesterday": Task.objects.filter(
                assigned_to=user,
                completed_at__date=today - timedelta(days=1),
                status="completed",
            ),
        }

        # Only send digest if there are tasks to report
        total_tasks = sum(tasks.count() for tasks in tasks_data.values())
        if total_tasks == 0:
            logger.info(f"No tasks to include in digest for user {user_id}")
            return {"status": "skipped", "reason": "no_tasks"}

        # Prepare email content
        context = {
            "user": user,
            "tasks_data": tasks_data,
            "date": today,
            "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
        }

        try:
            email_content = render_to_string("tasks/emails/daily_digest.html", context)
        except Exception:
            # Fallback to simple text email
            email_content = f"""
            Daily Task Digest for {today.strftime('%Y-%m-%d')}
            
            Overdue Tasks: {tasks_data['overdue'].count()}
            Due Today: {tasks_data['due_today'].count()}
            Due Tomorrow: {tasks_data['due_tomorrow'].count()}
            Completed Yesterday: {tasks_data['completed_yesterday'].count()}
            
            View all tasks: {context['site_url']}/tasks/
            """

        # Create communication record
        communication = Communication.objects.create(
            user=user,
            type="email",
            subject=f"Daily Task Digest - {today.strftime('%B %d, %Y')}",
            content=email_content,
            status="pending",
            is_notification=True,
        )

        # Send via email processing task
        from mobilize.communications.tasks import send_email_communication

        send_email_communication.delay(communication.id)

        logger.info(f"Queued daily task digest for user {user_id}")
        return {
            "status": "sent",
            "user_id": user_id,
            "total_tasks": total_tasks,
            "communication_id": communication.id,
        }

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {"status": "error", "reason": "user_not_found"}

    except Exception as exc:
        logger.error(f"Failed to send daily task digest for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def archive_old_task_notifications(self, days_to_keep: int = 30):
    """
    Archive old task notification communications.

    Args:
        days_to_keep: Number of days of notifications to keep active
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Archive old notification communications
        archived_count = Communication.objects.filter(
            is_notification=True, created_at__lt=cutoff_date, status="sent"
        ).update(archived=True)

        logger.info(f"Archived {archived_count} old task notifications")
        return {
            "archived_count": archived_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error archiving task notifications: {str(exc)}")
        raise self.retry(exc=exc)
