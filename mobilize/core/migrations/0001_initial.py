# Generated by Django 4.2 on 2025-06-16 13:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("admin_panel", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DashboardPreference",
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
                ("widget_config", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dashboard_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "dashboard_preferences",
            },
        ),
        migrations.CreateModel(
            name="ActivityLog",
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
                    "action_type",
                    models.CharField(
                        choices=[
                            ("create", "Create"),
                            ("update", "Update"),
                            ("delete", "Delete"),
                            ("view", "View"),
                            ("login", "Login"),
                            ("logout", "Logout"),
                            ("export", "Export"),
                            ("import", "Import"),
                            ("sync", "Synchronization"),
                            ("email", "Email"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=50,
                    ),
                ),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, null=True)),
                ("entity_type", models.CharField(blank=True, max_length=50, null=True)),
                ("entity_id", models.IntegerField(blank=True, null=True)),
                ("details", models.JSONField(blank=True, null=True)),
                (
                    "timestamp",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now
                    ),
                ),
                (
                    "office",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="activity_logs",
                        to="admin_panel.office",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="activity_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Activity Log",
                "verbose_name_plural": "Activity Logs",
                "db_table": "activity_logs",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(
                fields=["action_type"], name="activity_lo_action__9e4610_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(
                fields=["timestamp"], name="activity_lo_timesta_ef2c57_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(fields=["user"], name="activity_lo_user_id_072db3_idx"),
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(
                fields=["entity_type", "entity_id"],
                name="activity_lo_entity__5a4970_idx",
            ),
        ),
    ]
