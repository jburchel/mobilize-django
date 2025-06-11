"""
Supabase client integration for Django.

This module provides a wrapper around the Supabase Python client
to integrate with Django models and the SupabaseSync utility.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Type, Union

from django.db import models
from django.conf import settings
from supabase import create_client

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    A client for interacting with Supabase from Django.
    
    This is a placeholder implementation. The actual implementation
    will use the Supabase Python client.
    """
    
    def __init__(self):
        """Initialize the Supabase client."""
        # Try to get credentials from settings first, then fall back to environment variables
        self.supabase_url = getattr(settings, 'SUPABASE_URL', os.environ.get('SUPABASE_URL', ''))
        self.supabase_key = getattr(settings, 'SUPABASE_KEY', os.environ.get('SUPABASE_KEY', ''))
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning(
                "Supabase URL or key not found in settings or environment variables. "
                "Set SUPABASE_URL and SUPABASE_KEY for proper integration."
            )
            self.client = None
        else:
            try:
                # Initialize the actual Supabase client
                self.client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                self.client = None
    
    def get_table_name(self, model_class: Type[models.Model]) -> str:
        """
        Get the Supabase table name for a Django model.
        
        Args:
            model_class: The Django model class.
            
        Returns:
            The name of the corresponding Supabase table.
        """
        # Map Django model names to Supabase table names
        model_name = model_class.__name__
        
        # Explicit mapping for our core models
        model_to_table = {
            'Contact': 'contacts',
            'Person': 'people',
            'Church': 'churches',
        }
        
        if model_name in model_to_table:
            return model_to_table[model_name]
        
        # Fallback to model's db_table or the app_label + model_name
        if hasattr(model_class._meta, 'db_table') and model_class._meta.db_table:
            return model_class._meta.db_table
        
        # Last resort: lowercase and pluralize the model name
        return f"{model_name.lower()}s"
    
    def fetch_all(self, model_class: Type[models.Model], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all records for a model from Supabase.
        
        Args:
            model_class: The Django model class.
            limit: Optional limit on the number of records to fetch.
            
        Returns:
            A list of dictionaries representing the Supabase records.
        """
        table_name = self.get_table_name(model_class)
        logger.info(f"Fetching data from Supabase table: {table_name}")
        
        if not self.client:
            logger.error("Supabase client not initialized. Cannot fetch data.")
            return []
        
        try:
            # Use a direct select without any joins
            query = self.client.table(table_name).select('*')
            if limit:
                query = query.limit(limit)
                
            # Log the query for debugging
            logger.info(f"Executing Supabase query on table: {table_name}")
            
            response = query.execute()
            
            if hasattr(response, 'data'):
                logger.info(f"Successfully fetched {len(response.data)} records from {table_name}")
                return response.data
            logger.warning(f"No data returned from {table_name}")
            return []
        except Exception as e:
            logger.error(f"Error fetching data from Supabase: {str(e)}")
            return []
    
    def fetch_by_id(self, model_class: Type[models.Model], record_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Fetch a single record by ID from Supabase.
        
        Args:
            model_class: The Django model class.
            record_id: The ID of the record to fetch.
            
        Returns:
            A dictionary representing the Supabase record, or None if not found.
        """
        table_name = self.get_table_name(model_class)
        logger.info(f"Fetching record {record_id} from Supabase table: {table_name}")
        
        if not self.client:
            logger.error("Supabase client not initialized. Cannot fetch data.")
            return None
        
        try:
            response = self.client.table(table_name).select('*').eq('id', record_id).execute()
            
            if hasattr(response, 'data') and response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching record from Supabase: {str(e)}")
            return None
    
    def insert(self, model_class: Type[models.Model], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert a record into Supabase.
        
        Args:
            model_class: The Django model class.
            data: The data to insert.
            
        Returns:
            The inserted record as returned by Supabase, or None if the operation failed.
        """
        table_name = self.get_table_name(model_class)
        logger.info(f"Inserting record into Supabase table: {table_name}")
        
        if not self.client:
            logger.error("Supabase client not initialized. Cannot insert data.")
            return None
        
        try:
            response = self.client.table(table_name).insert(data).execute()
            
            if hasattr(response, 'data') and response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error inserting record into Supabase: {str(e)}")
            return None
    
    def update(self, model_class: Type[models.Model], record_id: Union[str, int], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a record in Supabase.
        
        Args:
            model_class: The Django model class.
            record_id: The ID of the record to update.
            data: The data to update.
            
        Returns:
            The updated record as returned by Supabase, or None if the operation failed.
        """
        table_name = self.get_table_name(model_class)
        logger.info(f"Updating record {record_id} in Supabase table: {table_name}")
        
        if not self.client:
            logger.error("Supabase client not initialized. Cannot update data.")
            return None
        
        try:
            response = self.client.table(table_name).update(data).eq('id', record_id).execute()
            
            if hasattr(response, 'data') and response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating record in Supabase: {str(e)}")
            return None
    
    def delete(self, model_class: Type[models.Model], record_id: Union[str, int]) -> bool:
        """
        Delete a record from Supabase.
        
        Args:
            model_class: The Django model class.
            record_id: The ID of the record to delete.
            
        Returns:
            True if the deletion was successful, False otherwise.
        """
        table_name = self.get_table_name(model_class)
        logger.info(f"Deleting record {record_id} from Supabase table: {table_name}")
        
        if not self.client:
            logger.error("Supabase client not initialized. Cannot delete data.")
            return False
        
        try:
            response = self.client.table(table_name).delete().eq('id', record_id).execute()
            return hasattr(response, 'data') and response.data is not None
        except Exception as e:
            logger.error(f"Error deleting record from Supabase: {str(e)}")
            return False


# Singleton instance for easy import
supabase = SupabaseClient()
