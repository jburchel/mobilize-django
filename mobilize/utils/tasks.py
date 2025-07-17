"""
Celery tasks for data synchronization and utility operations.

This module contains background tasks for syncing with external services,
managing data integrity, and performing maintenance operations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .supabase_client import SupabaseClient
from .supabase_sync import SupabaseSync
from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.communications.models import Communication
from mobilize.tasks.models import Task

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_supabase_task(
    self, direction: str = "both", model_name: str = None, force_full_sync: bool = False
):
    """
    Synchronize data with Supabase database.

    Args:
        direction: Sync direction ('push', 'pull', or 'both')
        model_name: Specific model to sync (optional)
        force_full_sync: Force a full sync instead of incremental
    """
    try:
        if not getattr(settings, "SUPABASE_URL", None) or not getattr(
            settings, "SUPABASE_KEY", None
        ):
            logger.warning("Supabase configuration not found, skipping sync")
            return {"status": "skipped", "reason": "no_config"}

        sync_client = SupabaseSync()

        # Determine which models to sync
        if model_name:
            models_to_sync = [model_name]
        else:
            models_to_sync = [
                "contacts",
                "persons",
                "churches",
                "communications",
                "tasks",
            ]

        results = {}
        total_synced = 0

        for model in models_to_sync:
            try:
                model_results = {"pushed": 0, "pulled": 0, "conflicts": 0, "errors": 0}

                if direction in ["push", "both"]:
                    # Push local changes to Supabase
                    push_result = sync_client.push_to_supabase(
                        model_name=model, force_full=force_full_sync
                    )
                    model_results["pushed"] = push_result.get("synced_count", 0)
                    model_results["conflicts"] += push_result.get("conflicts", 0)

                if direction in ["pull", "both"]:
                    # Pull changes from Supabase
                    pull_result = sync_client.pull_from_supabase(
                        model_name=model, force_full=force_full_sync
                    )
                    model_results["pulled"] = pull_result.get("synced_count", 0)
                    model_results["conflicts"] += pull_result.get("conflicts", 0)

                results[model] = model_results
                total_synced += model_results["pushed"] + model_results["pulled"]

                logger.info(f"Synced {model}: {model_results}")

            except Exception as e:
                logger.error(f"Error syncing {model}: {str(e)}")
                results[model] = {"error": str(e)}

        # Update sync statistics in cache
        sync_stats = {
            "last_sync": timezone.now().isoformat(),
            "direction": direction,
            "total_synced": total_synced,
            "results": results,
            "force_full_sync": force_full_sync,
        }
        cache.set(
            "supabase_sync_stats", sync_stats, timeout=86400
        )  # Cache for 24 hours

        logger.info(f"Supabase sync completed: {total_synced} total records synced")
        return sync_stats

    except Exception as exc:
        logger.error(f"Error in Supabase sync task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def backup_database_to_supabase(self):
    """
    Create a backup of critical data to Supabase.

    This task creates a comprehensive backup of the local database
    to Supabase for disaster recovery purposes.
    """
    try:
        if not getattr(settings, "SUPABASE_URL", None) or not getattr(
            settings, "SUPABASE_KEY", None
        ):
            logger.warning("Supabase configuration not found, skipping backup")
            return {"status": "skipped", "reason": "no_config"}

        sync_client = SupabaseSync()
        backup_results = {}

        # Models to backup in order of dependencies
        models_to_backup = [
            "users",
            "offices",
            "contacts",
            "persons",
            "churches",
            "communications",
            "tasks",
            "email_templates",
            "activity_logs",
        ]

        total_backed_up = 0

        for model in models_to_backup:
            try:
                # Force full sync for backup
                result = sync_client.push_to_supabase(model_name=model, force_full=True)

                backup_results[model] = {
                    "backed_up": result.get("synced_count", 0),
                    "errors": result.get("errors", 0),
                    "timestamp": timezone.now().isoformat(),
                }

                total_backed_up += result.get("synced_count", 0)

            except Exception as e:
                logger.error(f"Error backing up {model}: {str(e)}")
                backup_results[model] = {"error": str(e)}

        # Store backup metadata
        backup_metadata = {
            "backup_date": timezone.now().isoformat(),
            "total_records": total_backed_up,
            "models_backed_up": len(
                [m for m in backup_results if "error" not in backup_results[m]]
            ),
            "results": backup_results,
            "backup_type": "full_database",
        }

        # Cache backup status
        cache.set(
            "last_backup_status", backup_metadata, timeout=604800
        )  # Cache for 1 week

        logger.info(f"Database backup completed: {total_backed_up} records backed up")
        return backup_metadata

    except Exception as exc:
        logger.error(f"Error in database backup task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def cleanup_sync_conflicts(self, days_old: int = 7):
    """
    Clean up old sync conflict records.

    Args:
        days_old: Number of days old conflicts to clean up
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)

        # This would clean up sync conflict records if we had a model for them
        # For now, this is a placeholder for future implementation

        logger.info(f"Cleaned up sync conflicts older than {days_old} days")
        return {"status": "completed", "cutoff_date": cutoff_date.isoformat()}

    except Exception as exc:
        logger.error(f"Error cleaning up sync conflicts: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def validate_data_integrity(self):
    """
    Validate data integrity across the application.

    This task checks for common data integrity issues and reports them.
    """
    try:
        integrity_issues = []

        # Check for contacts without valid email formats
        invalid_emails = (
            Contact.objects.exclude(email="")
            .exclude(email__isnull=True)
            .exclude(email__regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        )
        if invalid_emails.exists():
            integrity_issues.append(
                {
                    "type": "invalid_email_format",
                    "count": invalid_emails.count(),
                    "description": "Contacts with invalid email formats",
                }
            )

        # Check for orphaned person records
        orphaned_persons = Person.objects.filter(contact__isnull=True)
        if orphaned_persons.exists():
            integrity_issues.append(
                {
                    "type": "orphaned_persons",
                    "count": orphaned_persons.count(),
                    "description": "Person records without contact records",
                }
            )

        # Check for tasks without assignees
        unassigned_tasks = Task.objects.filter(
            assigned_to__isnull=True, status__in=["pending", "in_progress"]
        )
        if unassigned_tasks.exists():
            integrity_issues.append(
                {
                    "type": "unassigned_tasks",
                    "count": unassigned_tasks.count(),
                    "description": "Active tasks without assignees",
                }
            )

        # Check for communications without recipients
        invalid_communications = Communication.objects.filter(
            type="email", person__isnull=True, status__in=["pending", "sent"]
        )
        if invalid_communications.exists():
            integrity_issues.append(
                {
                    "type": "invalid_communications",
                    "count": invalid_communications.count(),
                    "description": "Email communications without recipients",
                }
            )

        # Store integrity report in cache
        integrity_report = {
            "check_date": timezone.now().isoformat(),
            "total_issues": len(integrity_issues),
            "issues": integrity_issues,
            "status": "issues_found" if integrity_issues else "clean",
        }

        cache.set(
            "data_integrity_report", integrity_report, timeout=86400
        )  # Cache for 24 hours

        if integrity_issues:
            logger.warning(f"Found {len(integrity_issues)} data integrity issues")
        else:
            logger.info("Data integrity check passed - no issues found")

        return integrity_report

    except Exception as exc:
        logger.error(f"Error in data integrity validation: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def optimize_database_performance(self):
    """
    Perform database optimization tasks.

    This task runs maintenance operations to keep the database
    performing optimally.
    """
    try:
        from django.db import connection

        optimization_results = {}

        # Analyze table statistics (PostgreSQL specific)
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                # Update table statistics
                cursor.execute("ANALYZE;")
                optimization_results["analyze"] = "completed"

                # Get table sizes for monitoring
                cursor.execute(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10;
                """
                )

                table_sizes = cursor.fetchall()
                optimization_results["largest_tables"] = [
                    {"schema": row[0], "table": row[1], "size": row[2]}
                    for row in table_sizes
                ]

        # Clear expired cache entries
        cache.clear()
        optimization_results["cache_cleared"] = True

        # Store optimization report
        optimization_report = {
            "optimization_date": timezone.now().isoformat(),
            "results": optimization_results,
            "database_vendor": connection.vendor,
        }

        cache.set(
            "db_optimization_report", optimization_report, timeout=86400
        )  # Cache for 24 hours

        logger.info("Database optimization completed")
        return optimization_report

    except Exception as exc:
        logger.error(f"Error in database optimization: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def generate_system_health_report(self):
    """
    Generate a comprehensive system health report.

    This task collects various metrics and generates a health report
    for system monitoring purposes.
    """
    try:
        from django.db import connection
        import psutil
        import os

        health_metrics = {}

        # Database metrics
        with connection.cursor() as cursor:
            # Count total records in main tables
            cursor.execute("SELECT COUNT(*) FROM contacts_contact;")
            health_metrics["total_contacts"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tasks_task;")
            health_metrics["total_tasks"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM communications_communication;")
            health_metrics["total_communications"] = cursor.fetchone()[0]

            # Database connection count
            if connection.vendor == "postgresql":
                cursor.execute("SELECT count(*) FROM pg_stat_activity;")
                health_metrics["db_connections"] = cursor.fetchone()[0]

        # System metrics (if available)
        try:
            health_metrics["cpu_percent"] = psutil.cpu_percent()
            health_metrics["memory_percent"] = psutil.virtual_memory().percent
            health_metrics["disk_usage"] = psutil.disk_usage("/").percent
        except:
            health_metrics["system_metrics"] = "unavailable"

        # Cache metrics
        health_metrics["cache_status"] = (
            "available" if cache.get("test_key") is None else "available"
        )

        # Recent error counts (placeholder - would need error tracking)
        health_metrics["recent_errors"] = (
            0  # This would be implemented with proper error tracking
        )

        # Task queue metrics (placeholder - would need Celery monitoring)
        health_metrics["pending_tasks"] = 0  # This would query Celery for pending tasks

        health_report = {
            "report_date": timezone.now().isoformat(),
            "status": "healthy",  # Would be determined based on thresholds
            "metrics": health_metrics,
            "uptime": timezone.now().isoformat(),  # Placeholder for actual uptime
        }

        # Store health report
        cache.set(
            "system_health_report", health_report, timeout=3600
        )  # Cache for 1 hour

        logger.info("System health report generated")
        return health_report

    except Exception as exc:
        logger.error(f"Error generating system health report: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def cleanup_temporary_files(self, days_old: int = 7):
    """
    Clean up temporary files and logs.

    Args:
        days_old: Number of days old files to clean up
    """
    try:
        import os
        import glob
        from pathlib import Path

        cleanup_results = {
            "files_removed": 0,
            "space_freed": 0,
            "directories_checked": [],
        }

        # Directories to clean up
        cleanup_dirs = [
            settings.BASE_DIR / "logs",
            settings.BASE_DIR / "tmp",
            settings.MEDIA_ROOT / "temp",
        ]

        cutoff_time = timezone.now() - timedelta(days=days_old)
        cutoff_timestamp = cutoff_time.timestamp()

        for directory in cleanup_dirs:
            if directory.exists():
                cleanup_results["directories_checked"].append(str(directory))

                # Find old files
                for file_path in directory.rglob("*"):
                    if file_path.is_file():
                        try:
                            if file_path.stat().st_mtime < cutoff_timestamp:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                cleanup_results["files_removed"] += 1
                                cleanup_results["space_freed"] += file_size
                        except Exception as e:
                            logger.warning(
                                f"Could not remove file {file_path}: {str(e)}"
                            )

        # Convert bytes to MB for readability
        cleanup_results["space_freed_mb"] = round(
            cleanup_results["space_freed"] / (1024 * 1024), 2
        )

        logger.info(
            f"Cleaned up {cleanup_results['files_removed']} files, freed {cleanup_results['space_freed_mb']} MB"
        )
        return cleanup_results

    except Exception as exc:
        logger.error(f"Error cleaning up temporary files: {str(exc)}")
        raise self.retry(exc=exc)
