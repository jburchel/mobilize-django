"""
Supabase Synchronization Utility

This module provides utilities for synchronizing data between Django models and Supabase.
It uses the SupabaseMapper to handle field name differences and type conversions.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Type, Optional

from django.db import models, transaction
from django.utils import timezone

from .supabase_mapper import SupabaseMapper
from .supabase_client import supabase

logger = logging.getLogger(__name__)


class SupabaseSync:
    """
    A utility class for synchronizing data between Django models and Supabase.
    """

    @classmethod
    def sync_to_supabase(cls, instance: models.Model) -> Optional[Dict[str, Any]]:
        """
        Synchronize a Django model instance to Supabase.

        Args:
            instance: Django model instance to synchronize

        Returns:
            Dictionary with data in Supabase format if successful, None otherwise
        """
        # Convert the instance to Supabase format
        supabase_data = SupabaseMapper.to_supabase(instance)

        # Update the last_synced_at field
        supabase_data["last_synced_at"] = datetime.now().date().isoformat()

        # Use the Supabase client to send the data
        model_class = instance.__class__
        instance_id = getattr(instance, "id", None)

        try:
            if instance_id:
                # Check if the record exists in Supabase
                existing_record = supabase.fetch_by_id(model_class, instance_id)

                if existing_record:
                    # Update existing record
                    result = supabase.update(model_class, instance_id, supabase_data)
                    logger.info(
                        f"Updated {model_class.__name__} with ID {instance_id} in Supabase"
                    )
                else:
                    # Insert new record with specified ID
                    result = supabase.insert(model_class, supabase_data)
                    logger.info(
                        f"Inserted {model_class.__name__} with ID {instance_id} into Supabase"
                    )
            else:
                # Insert new record without ID
                result = supabase.insert(model_class, supabase_data)
                logger.info(f"Inserted new {model_class.__name__} into Supabase")

            return result
        except Exception as e:
            logger.error(f"Error syncing {model_class.__name__} to Supabase: {str(e)}")
            return None

    @classmethod
    def sync_from_supabase(
        cls, supabase_data: Dict[str, Any], model_class: Type[models.Model]
    ) -> Optional[models.Model]:
        """
        Synchronize data from Supabase to a Django model.

        Args:
            supabase_data: Dictionary of data from Supabase
            model_class: Django model class

        Returns:
            Updated or created Django model instance, or None if sync failed
        """
        try:
            # Import models here to avoid circular imports
            from mobilize.contacts.models import Contact, Person
            from mobilize.churches.models import Church

            # Convert the data to Django format
            django_data = SupabaseMapper.from_supabase(supabase_data, model_class)

            # Check if the instance already exists
            instance_id = django_data.get("id")
            instance = None

            if instance_id:
                try:
                    instance = model_class.objects.get(id=instance_id)
                except model_class.DoesNotExist:
                    instance = None

            # Special handling for multi-table inheritance
            if model_class in [Person, Church]:
                # First, make sure the Contact record exists
                contact_instance = None
                try:
                    if instance_id:
                        contact_instance = Contact.objects.get(id=instance_id)
                except Contact.DoesNotExist:
                    # Need to create the Contact record first
                    contact_fields = [
                        f.name for f in Contact._meta.fields if f.name != "id"
                    ]
                    contact_data = {
                        k: v for k, v in django_data.items() if k in contact_fields
                    }

                    try:
                        # Create the Contact record with the correct ID
                        if instance_id:
                            contact_instance = Contact(id=instance_id, **contact_data)
                            contact_instance.save()
                        else:
                            contact_instance = Contact.objects.create(**contact_data)
                        logger.info(
                            f"Created Contact record with ID {contact_instance.id} for {model_class.__name__}"
                        )
                    except Exception as contact_error:
                        logger.error(
                            f"Error creating Contact record: {str(contact_error)}"
                        )
                        # Try a more selective approach with minimal data
                        if instance_id:
                            contact_instance = Contact(id=instance_id)
                            contact_instance.save()
                        else:
                            contact_instance = Contact.objects.create()
                        logger.info(
                            f"Created minimal Contact record with ID {contact_instance.id}"
                        )

                # Now we can update or create the actual model instance
                if instance:
                    # Update existing instance
                    model_fields = [
                        f.name
                        for f in model_class._meta.fields
                        if f.name != "contact_ptr"
                    ]
                    for field_name, field_value in django_data.items():
                        if field_name in model_fields and hasattr(instance, field_name):
                            setattr(instance, field_name, field_value)

                    # Update the last_synced_at field if it exists
                    if hasattr(instance, "last_synced_at"):
                        instance.last_synced_at = timezone.now().date()

                    instance.save()
                    logger.info(
                        f"Updated {model_class.__name__} with ID {instance_id} from Supabase"
                    )
                else:
                    # Create new instance
                    try:
                        # For inherited models, we need to use raw SQL to bypass Django's ORM constraints
                        # This is because Django expects contact_ptr_id to be the primary key
                        model_fields = [
                            f.name
                            for f in model_class._meta.fields
                            if f.name != "contact_ptr"
                        ]
                        model_data = {
                            k: v for k, v in django_data.items() if k in model_fields
                        }

                        # Create the instance directly with raw SQL
                        table_name = model_class._meta.db_table
                        fields = list(model_data.keys())
                        placeholders = ["%s"] * len(fields)
                        values = [model_data[field] for field in fields]

                        # Add the contact_ptr_id field
                        fields.append("contact_ptr_id")
                        placeholders.append("%s")
                        values.append(contact_instance.id)

                        # Execute the SQL
                        from django.db import connection

                        with connection.cursor() as cursor:
                            sql = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                            cursor.execute(sql, values)

                        # Now retrieve the created instance
                        instance = model_class.objects.get(id=contact_instance.id)
                        logger.info(
                            f"Created new {model_class.__name__} with ID {instance.id} from Supabase"
                        )
                    except Exception as create_error:
                        logger.error(
                            f"Error creating {model_class.__name__} with raw SQL: {str(create_error)}"
                        )
                        # Fall back to using Django's ORM with a direct update to the database
                        try:
                            # Create a minimal instance
                            instance = model_class(contact_ptr_id=contact_instance.id)
                            instance.save()

                            # Update it with the actual data
                            for field_name, field_value in model_data.items():
                                if hasattr(instance, field_name):
                                    setattr(instance, field_name, field_value)
                            instance.save()
                            logger.info(
                                f"Created new {model_class.__name__} with ID {instance.id} using fallback method"
                            )
                        except Exception as fallback_error:
                            logger.error(
                                f"Fallback creation failed: {str(fallback_error)}"
                            )
                            return None
            else:
                # Standard handling for non-inherited models
                with transaction.atomic():
                    if instance:
                        # Update existing instance
                        for field_name, field_value in django_data.items():
                            # Skip fields that don't exist on the model
                            if hasattr(instance, field_name):
                                setattr(instance, field_name, field_value)

                        # Update the last_synced_at field if it exists
                        if hasattr(instance, "last_synced_at"):
                            instance.last_synced_at = timezone.now().date()
                        instance.save()
                        logger.info(
                            f"Updated {model_class.__name__} with ID {instance_id} from Supabase"
                        )
                    else:
                        # Create new instance
                        try:
                            instance = model_class(**django_data)
                            instance.save()
                            logger.info(
                                f"Created new {model_class.__name__} with ID {instance.id} from Supabase"
                            )
                        except Exception as create_error:
                            logger.error(
                                f"Error creating {model_class.__name__}: {str(create_error)}"
                            )
                            # Try a more selective approach with only fields that exist on the model
                            filtered_data = {
                                k: v
                                for k, v in django_data.items()
                                if k in [f.name for f in model_class._meta.fields]
                            }
                            instance = model_class.objects.create(**filtered_data)
                            logger.info(
                                f"Created new {model_class.__name__} with ID {instance.id} from Supabase (filtered fields)"
                            )

            return instance
        except Exception as e:
            logger.error(
                f"Error syncing {model_class.__name__} from Supabase: {str(e)}"
            )
            return None

            return instance
        except Exception as e:
            logger.error(
                f"Error syncing {model_class.__name__} from Supabase: {str(e)}"
            )
            return None

    @classmethod
    def bulk_sync_to_supabase(
        cls, instances: List[models.Model]
    ) -> List[Dict[str, Any]]:
        """
        Synchronize multiple Django model instances to Supabase.

        Args:
            instances: List of Django model instances to synchronize

        Returns:
            List of dictionaries with data in Supabase format
        """
        supabase_data_list = []

        for instance in instances:
            supabase_data = cls.sync_to_supabase(instance)
            if supabase_data:
                supabase_data_list.append(supabase_data)

        return supabase_data_list

    @classmethod
    def bulk_sync_from_supabase(
        cls, supabase_data_list: List[Dict[str, Any]], model_class: Type[models.Model]
    ) -> List[models.Model]:
        """
        Synchronize multiple records from Supabase to Django models.

        Args:
            supabase_data_list: List of dictionaries with data from Supabase
            model_class: Django model class

        Returns:
            List of updated or created Django model instances
        """
        instances = []

        for supabase_data in supabase_data_list:
            instance = cls.sync_from_supabase(supabase_data, model_class)
            if instance:
                instances.append(instance)

        return instances

    @classmethod
    def detect_conflicts(
        cls, instance: models.Model, supabase_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect conflicts between a Django model instance and Supabase data.

        Args:
            instance: Django model instance
            supabase_data: Dictionary of data from Supabase

        Returns:
            Dictionary with conflict information
        """
        conflicts = {}

        # Convert the Supabase data to Django format
        django_data = SupabaseMapper.from_supabase(supabase_data, instance.__class__)

        # Compare fields
        for field_name, field_value in django_data.items():
            if hasattr(instance, field_name):
                instance_value = getattr(instance, field_name)

                # Skip comparison for certain fields
                if field_name in ["last_synced_at", "updated_at", "date_modified"]:
                    continue

                # Compare values
                if instance_value != field_value and field_value is not None:
                    conflicts[field_name] = {
                        "django_value": instance_value,
                        "supabase_value": field_value,
                    }

        return conflicts

    @classmethod
    def resolve_conflicts(
        cls,
        instance: models.Model,
        conflicts: Dict[str, Dict[str, Any]],
        resolution_strategy: str = "django",
    ) -> models.Model:
        """
        Resolve conflicts between a Django model instance and Supabase data.

        Args:
            instance: Django model instance
            conflicts: Dictionary with conflict information
            resolution_strategy: Strategy for resolving conflicts ('django' or 'supabase')

        Returns:
            Updated Django model instance
        """
        with transaction.atomic():
            for field_name, conflict_info in conflicts.items():
                if resolution_strategy == "supabase":
                    # Use the value from Supabase
                    setattr(instance, field_name, conflict_info["supabase_value"])
                # If resolution_strategy is 'django', keep the Django value

            # Mark conflicts as resolved
            instance.has_conflict = False
            instance.conflict_data = None

            # Update the last_synced_at field
            instance.last_synced_at = timezone.now().date()
            instance.save()

        return instance
