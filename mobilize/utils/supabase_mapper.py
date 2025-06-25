"""
Supabase Mapper Utility

This module provides utilities for mapping between Django models and Supabase schema.
It handles field name differences and type conversions when interacting with Supabase.
"""

from typing import Dict, Any, Type, List
from django.db import models
from django.db.models.query import QuerySet


class SupabaseMapper:
    """
    A utility class for mapping between Django models and Supabase schema.
    """

    # Field name mapping from Django model field to Supabase column
    FIELD_MAPPING = {
        'Church': {
            # Church fields are mostly aligned with Supabase
        },
        'Person': {
            # Person-specific field mappings
            'user_id': 'user_id',  # Note: In Person, user_id is character varying in Supabase
        },
        'Contact': {
            # Contact fields are mostly aligned with Supabase
        }
    }

    # Field type mapping for special cases
    TYPE_MAPPING = {
        # Model-specific type conversions
        'Person.user_id': {
            'to_supabase': lambda x: str(x) if x is not None else None,
            'from_supabase': lambda x: int(x) if x is not None and x != '' else None
        },
        'Contact.user_id': {
            'to_supabase': lambda x: str(x) if x is not None else None,
            'from_supabase': lambda x: int(x) if x is not None and x != '' else None
        },
        'office_id': {
            'to_supabase': lambda x: str(x) if x is not None else None,
            'from_supabase': lambda x: int(x) if x is not None and x != '' else None
        },
        'church_id': {
            'to_supabase': lambda x: str(x) if x is not None else None,
            'from_supabase': lambda x: int(x) if x is not None and x != '' else None
        },
        'main_contact_id': {
            'to_supabase': lambda x: str(x) if x is not None else None,
            'from_supabase': lambda x: int(x) if x is not None and x != '' else None
        },
        # Boolean conversions
        'has_conflict': {
            'to_supabase': lambda x: bool(x) if x is not None else None,
            'from_supabase': lambda x: bool(x) if x is not None else None
        },
        'virtuous': {
            'to_supabase': lambda x: bool(x) if x is not None else None,
            'from_supabase': lambda x: bool(x) if x is not None else None
        },
        'is_primary_contact': {
            'to_supabase': lambda x: bool(x) if x is not None else None,
            'from_supabase': lambda x: bool(x) if x is not None else None
        }
    }

    @classmethod
    def to_supabase(cls, instance: models.Model) -> Dict[str, Any]:
        """
        Convert a Django model instance to a Supabase-compatible dictionary.
        
        Args:
            instance: Django model instance
            
        Returns:
            Dictionary with field names and values mapped to Supabase schema
        """
        model_name = instance.__class__.__name__
        data = {}
        
        # Get all fields from the model
        for field in instance._meta.fields:
            field_name = field.name
            field_value = getattr(instance, field_name)
            
            # Apply field name mapping if exists
            supabase_field_name = cls.FIELD_MAPPING.get(model_name, {}).get(field_name, field_name)
            
            # Apply type conversion if needed
            model_field_key = f"{model_name}.{field_name}"
            if model_field_key in cls.TYPE_MAPPING:
                field_value = cls.TYPE_MAPPING[model_field_key]['to_supabase'](field_value)
            elif field_name in cls.TYPE_MAPPING:
                field_value = cls.TYPE_MAPPING[field_name]['to_supabase'](field_value)
            
            data[supabase_field_name] = field_value
            
            # For ForeignKey fields, also include the _id field that Supabase expects
            if hasattr(field, 'related_model') and field.related_model is not None:
                # This is a ForeignKey field
                id_field_name = f"{field_name}_id"
                id_value = getattr(instance, id_field_name, None)
                
                # Apply type conversion for ID fields
                model_id_field_key = f"{model_name}.{id_field_name}"
                if model_id_field_key in cls.TYPE_MAPPING:
                    id_value = cls.TYPE_MAPPING[model_id_field_key]['to_supabase'](id_value)
                elif id_field_name in cls.TYPE_MAPPING:
                    id_value = cls.TYPE_MAPPING[id_field_name]['to_supabase'](id_value)
                
                data[id_field_name] = id_value
            
        return data
    
    @classmethod
    def from_supabase(cls, supabase_data: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Convert Supabase data to Django model format.
        
        Args:
            supabase_data: Dictionary of data from Supabase
            model_class: Django model class or string name of the model
            
        Returns:
            Dictionary with field names and values in Django format
        """
        django_data = {}
        
        # Handle string model names
        if isinstance(model_class, str):
            model_name = model_class
        else:
            model_name = model_class.__name__
        
        # Get the reverse field mapping for this model
        field_mapping_reverse = {}
        if model_name in cls.FIELD_MAPPING:
            field_mapping_reverse = {v: k for k, v in cls.FIELD_MAPPING[model_name].items()}
        # Apply field name mapping and type conversions
        for field_name, field_value in supabase_data.items():
            # Apply field name mapping if exists
            django_field_name = field_mapping_reverse.get(field_name, field_name)
            
            # Skip field validation if model_class is a string
            if not isinstance(model_class, str):
                # Skip fields that don't exist in the model
                if not hasattr(model_class, django_field_name) and not any(f.name == django_field_name for f in model_class._meta.fields):
                    continue
                
            # Apply type conversion if needed
            model_field_key = f"{model_name}.{django_field_name}"
            if model_field_key in cls.TYPE_MAPPING:
                field_value = cls.TYPE_MAPPING[model_field_key]['from_supabase'](field_value)
            elif django_field_name in cls.TYPE_MAPPING:
                field_value = cls.TYPE_MAPPING[django_field_name]['from_supabase'](field_value)
                
            django_data[django_field_name] = field_value
            
        return django_data
    
    @classmethod
    def bulk_to_supabase(cls, django_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert a list of Django data dictionaries to Supabase format.
        
        Args:
            django_data_list: List of dictionaries with Django data
            
        Returns:
            List of dictionaries with data in Supabase format
        """
        result = []
        for item in django_data_list:
            supabase_item = {}
            # Apply field name mapping and type conversions
            for field_name, field_value in item.items():
                # Apply type conversion if needed
                if field_name in cls.TYPE_MAPPING:
                    field_value = cls.TYPE_MAPPING[field_name]['to_supabase'](field_value)
                
                supabase_item[field_name] = field_value
            result.append(supabase_item)
        return result
    
    @classmethod
    def bulk_from_supabase(cls, supabase_data_list: List[Dict[str, Any]], model_class) -> List[Dict[str, Any]]:
        """
        Convert a list of Supabase data dictionaries to Django format.
        
        Args:
            supabase_data_list: List of dictionaries with Supabase data
            model_class: Django model class or string name of the model
            
        Returns:
            List of dictionaries with data in Django format
        """
        return [cls.from_supabase(item, model_class) for item in supabase_data_list]
    
    @classmethod
    def create_from_supabase(cls, data: Dict[str, Any], model_class: Type[models.Model]) -> models.Model:
        """
        Create a new model instance from Supabase data.
        
        Args:
            data: Dictionary from Supabase
            model_class: Django model class
            
        Returns:
            New model instance
        """
        django_data = cls.from_supabase(data, model_class)
        instance = model_class.objects.create(**django_data)
        return instance
    
    @classmethod
    def update_from_supabase(cls, instance: models.Model, data: Dict[str, Any]) -> models.Model:
        """
        Update a model instance from Supabase data.
        
        Args:
            instance: Model instance to update
            data: Dictionary from Supabase
            
        Returns:
            Updated model instance
        """
        django_data = cls.from_supabase(data, instance.__class__)
        
        for field_name, field_value in django_data.items():
            setattr(instance, field_name, field_value)
            
        instance.save()
        return instance
    
    @classmethod
    def bulk_create_from_supabase(cls, data_list: List[Dict[str, Any]], model_class: Type[models.Model]) -> List[models.Model]:
        """
        Create multiple Django model instances from Supabase data.
        
        Args:
            data_list: List of dictionaries from Supabase
            model_class: Django model class
            
        Returns:
            List of new Django model instances
        """
        instances = []
        
        for data in data_list:
            mapped_data = cls.from_supabase(data, model_class)
            instances.append(model_class(**mapped_data))
            
        return model_class.objects.bulk_create(instances)
    
    @classmethod
    def to_supabase_queryset(cls, queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Convert a Django queryset to a list of Supabase-compatible dictionaries.
        
        Args:
            queryset: Django queryset
            
        Returns:
            List of dictionaries with field names and values mapped to Supabase schema
        """
        result = []
        
        for instance in queryset:
            result.append(cls.to_supabase(instance))
            
        return result
