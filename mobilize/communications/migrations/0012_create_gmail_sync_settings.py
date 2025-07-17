# Generated manually for GmailSyncSettings model

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("communications", "0011_fix_timestamp_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GmailSyncSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "auto_sync_enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Enable automatic Gmail syncing for this user",
                    ),
                ),
                (
                    "sync_frequency_hours",
                    models.IntegerField(
                        default=1, help_text="How often to sync Gmail in hours"
                    ),
                ),
                (
                    "contacts_only",
                    models.BooleanField(
                        default=True,
                        help_text="Only sync emails from/to known contacts",
                    ),
                ),
                (
                    "days_back_on_sync",
                    models.IntegerField(
                        default=7, help_text="Number of days back to check on each sync"
                    ),
                ),
                (
                    "last_sync_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp of last successful sync",
                        null=True,
                    ),
                ),
                (
                    "sync_errors",
                    models.TextField(
                        blank=True,
                        help_text="Last sync error message, if any",
                        null=True,
                    ),
                ),
                (
                    "total_emails_synced",
                    models.IntegerField(
                        default=0,
                        help_text="Total number of emails synced for this user",
                    ),
                ),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gmail_sync_settings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Gmail Sync Settings",
                "verbose_name_plural": "Gmail Sync Settings",
                "db_table": "gmail_sync_settings",
            },
        ),
    ]
