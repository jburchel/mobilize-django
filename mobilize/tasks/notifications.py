import datetime
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail  # For actual email sending later
from django.contrib.sites.models import Site

from .models import Task


def get_reminder_trigger_time(task):
    """Calculates the absolute datetime when a reminder should be triggered."""
    if not task.due_date or task.reminder_option == "none":
        return None

    # Default due time to 00:00 if not set, for date-based calculations
    if task.due_time:
        # Handle case where due_time might be a string (from CharField)
        if isinstance(task.due_time, str):
            try:
                effective_due_time = datetime.datetime.strptime(
                    task.due_time, "%H:%M"
                ).time()
            except ValueError:
                # If parsing fails, default to midnight
                effective_due_time = datetime.time.min
        else:
            effective_due_time = task.due_time
    else:
        effective_due_time = datetime.time.min

    base_due_datetime = timezone.make_aware(
        datetime.datetime.combine(task.due_date, effective_due_time),
        timezone.get_default_timezone(),  # Assumes server timezone; consider task-specific timezone if available
    )

    reminder_trigger_time = None

    if task.reminder_option == "on_due_time":
        reminder_trigger_time = base_due_datetime
    elif task.reminder_option == "5_min_before":
        reminder_trigger_time = base_due_datetime - datetime.timedelta(minutes=5)
    elif task.reminder_option == "15_min_before":
        reminder_trigger_time = base_due_datetime - datetime.timedelta(minutes=15)
    elif task.reminder_option == "30_min_before":
        reminder_trigger_time = base_due_datetime - datetime.timedelta(minutes=30)
    elif task.reminder_option == "1_hour_before":
        reminder_trigger_time = base_due_datetime - datetime.timedelta(hours=1)
    elif task.reminder_option == "2_hours_before":
        reminder_trigger_time = base_due_datetime - datetime.timedelta(hours=2)
    elif task.reminder_option == "2_days_before":
        reminder_trigger_time = base_due_datetime - datetime.timedelta(days=2)
    elif task.reminder_option == "1_week_before":
        reminder_trigger_time = base_due_datetime - datetime.timedelta(weeks=1)
    elif task.reminder_option == "1_day_before":
        # Reminder at 9 AM on the day before
        reminder_date = task.due_date - datetime.timedelta(days=1)
        reminder_trigger_time = timezone.make_aware(
            datetime.datetime.combine(reminder_date, datetime.time(9, 0)),
            timezone.get_default_timezone(),
        )
    elif task.reminder_option == "custom_on_due_date" and task.reminder_time:
        # Custom reminder time on the due_date
        if isinstance(task.reminder_time, str):
            try:
                reminder_time_obj = datetime.datetime.strptime(
                    task.reminder_time, "%H:%M"
                ).time()
            except ValueError:
                reminder_time_obj = datetime.time(
                    9, 0
                )  # Default to 9 AM if parsing fails
        else:
            reminder_time_obj = task.reminder_time
        reminder_trigger_time = timezone.make_aware(
            datetime.datetime.combine(task.due_date, reminder_time_obj),
            timezone.get_default_timezone(),
        )

    return reminder_trigger_time


def get_tasks_needing_reminders():
    """Identifies tasks that are due for a reminder."""
    now = timezone.now()
    tasks_to_remind = []

    potential_tasks = Task.objects.filter(
        status__ne=Task.STATUS_CHOICES[2][0],  # Not 'completed'
        due_date__isnull=False,
        reminder_option__isnull=False,
        reminder_sent=False,  # Reminder not yet sent
    ).exclude(reminder_option="none")

    for task in potential_tasks:
        reminder_trigger_time = get_reminder_trigger_time(task)

        if reminder_trigger_time and now >= reminder_trigger_time:
            # Ensure we don't send reminders for tasks too far in the past if reminder_sent flag failed
            # For example, only send if the reminder time was within the last 24 hours (or some reasonable window)
            # Or, more simply, if the task itself is not long past due.
            if task.due_date >= now.date() or (
                task.due_date == now.date() - datetime.timedelta(days=1)
                and reminder_trigger_time.date() == now.date()
            ):
                tasks_to_remind.append(task)

    return tasks_to_remind


def send_due_date_notifications():
    """Sends (or simulates sending) notifications for tasks needing reminders."""
    tasks = get_tasks_needing_reminders()
    notifications_sent_count = 0

    # Get current site for constructing absolute URLs
    # Fallback if sites framework is not configured for some reason
    try:
        current_site = Site.objects.get_current()
        domain = current_site.domain
    except Exception:  # Broad exception for safety in background task
        domain = getattr(
            settings, "SITE_DOMAIN", "localhost:8000"
        )  # Fallback to settings or default

    for task in tasks:
        if task.assigned_to and task.assigned_to.email:
            subject = f"Task Reminder: {task.title}"
            task_url = (
                f"http://{domain}{task.get_absolute_url()}"  # Ensure scheme if needed
            )
            message = (
                f"Hi {task.assigned_to.get_full_name() or task.assigned_to.username},\n\n"
                f"This is a reminder for your task: '{task.title}'.\n"
                f"It is due on {task.due_date.strftime('%Y-%m-%d')}"
                f"{' at ' + (task.due_time if isinstance(task.due_time, str) else task.due_time.strftime('%H:%M')) if task.due_time else ''}.\n\n"
                f"Details: {task.description or 'N/A'}\n\n"
                f"You can view the task here: {task_url}\n\n"
                f"Thanks,\nThe Mobilize Team"
            )
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")

            try:
                # send_mail(subject, message, from_email, [task.assigned_to.email]) # Uncomment for actual sending
                print(
                    f"Simulating email to {task.assigned_to.email} for task ID {task.id}: {task.title}"
                )
                task.reminder_sent = True
                task.save(update_fields=["reminder_sent", "updated_at"])
                notifications_sent_count += 1
            except Exception as e:
                print(f"Error sending reminder for task {task.id}: {e}")  # Log this

    return notifications_sent_count
