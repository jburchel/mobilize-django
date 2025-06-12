"""
Tests for core models validation and constraints
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from mobilize.core.models import ActivityLog
from mobilize.admin_panel.models import Office
from mobilize.contacts.models import Person
from datetime import datetime, timedelta
import json

User = get_user_model()


class ActivityLogModelValidationTests(TestCase):
    """Test cases for ActivityLog model validation and constraints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='standard_user'
        )
        
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST001'
        )
        
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            user_id=self.user.id
        )
    
    def test_activity_log_creation_with_required_fields(self):
        """Test creating activity log with only required fields"""
        log = ActivityLog.objects.create(
            action_type='view',
            entity_type='person',
            entity_id=self.person.id
        )
        
        self.assertEqual(log.action_type, 'view')
        self.assertEqual(log.entity_type, 'person')
        self.assertEqual(log.entity_id, self.person.id)
        self.assertIsNotNone(log.timestamp)
        self.assertIsNone(log.user)
        self.assertIsNone(log.office)
    
    def test_activity_log_creation_with_all_fields(self):
        """Test creating activity log with all fields"""
        details = {'ip': '127.0.0.1', 'message': 'Test action'}
        
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='create',
            entity_type='person',
            entity_id=self.person.id,
            office=self.office,
            details=details,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 Test Browser'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'create')
        self.assertEqual(log.entity_type, 'person')
        self.assertEqual(log.entity_id, self.person.id)
        self.assertEqual(log.office, self.office)
        self.assertEqual(log.details, details)
        self.assertEqual(log.ip_address, '192.168.1.1')
        self.assertEqual(log.user_agent, 'Mozilla/5.0 Test Browser')
    
    def test_activity_log_action_choices(self):
        """Test all valid action type choices"""
        valid_actions = [
            'create', 'update', 'delete', 'view', 'login', 
            'logout', 'export', 'import', 'sync', 'email', 'other'
        ]
        
        for action in valid_actions:
            log = ActivityLog.objects.create(
                action_type=action,
                entity_type='test',
                entity_id=1
            )
            self.assertEqual(log.action_type, action)
            # Just verify the action type was set correctly
            self.assertEqual(log.action_type, action)
    
    def test_activity_log_string_representation_with_user(self):
        """Test ActivityLog __str__ method with user"""
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='create',
            entity_type='person',
            entity_id=self.person.id
        )
        
        str_repr = str(log)
        self.assertIn(self.user.email, str_repr)  # Uses email as fallback
        self.assertIn('Create', str_repr)
        self.assertIn('person', str_repr)
        self.assertIn(str(self.person.id), str_repr)
    
    def test_activity_log_string_representation_without_user(self):
        """Test ActivityLog __str__ method without user"""
        log = ActivityLog.objects.create(
            action_type='sync',
            entity_type='system'
        )
        
        str_repr = str(log)
        self.assertIn('System', str_repr)
        self.assertIn('Sync', str_repr)
        self.assertIn('system', str_repr)
    
    def test_activity_log_string_representation_with_full_name(self):
        """Test ActivityLog __str__ method with user having full name"""
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='update',
            entity_type='contact'
        )
        
        str_repr = str(log)
        self.assertIn('John Doe', str_repr)
        self.assertIn('Update', str_repr)
    
    def test_activity_log_json_details_field(self):
        """Test ActivityLog details JSONField functionality"""
        complex_details = {
            'changes': {
                'first_name': {'old': 'John', 'new': 'Johnny'},
                'email': {'old': 'john@old.com', 'new': 'johnny@new.com'}
            },
            'ip_address': '127.0.0.1',
            'user_agent': 'Chrome/91.0',
            'timestamp': '2024-01-01T10:00:00Z'
        }
        
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='update',
            entity_type='person',
            entity_id=self.person.id,
            details=complex_details
        )
        
        # Refresh from database
        log.refresh_from_db()
        
        self.assertEqual(log.details['changes']['first_name']['old'], 'John')
        self.assertEqual(log.details['changes']['first_name']['new'], 'Johnny')
        self.assertEqual(log.details['ip_address'], '127.0.0.1')
        self.assertEqual(log.details['user_agent'], 'Chrome/91.0')
    
    def test_activity_log_ordering(self):
        """Test ActivityLog default ordering by timestamp descending"""
        # Create logs with slight time differences
        log1 = ActivityLog.objects.create(
            action_type='create',
            entity_type='test1'
        )
        
        log2 = ActivityLog.objects.create(
            action_type='create',
            entity_type='test2'
        )
        
        logs = list(ActivityLog.objects.all())
        
        # Most recent should be first
        self.assertEqual(logs[0], log2)
        self.assertEqual(logs[1], log1)
    
    def test_activity_log_db_table_name(self):
        """Test ActivityLog uses correct database table name"""
        self.assertEqual(ActivityLog._meta.db_table, 'activity_logs')
    
    def test_activity_log_verbose_names(self):
        """Test ActivityLog verbose names"""
        self.assertEqual(ActivityLog._meta.verbose_name, 'Activity Log')
        self.assertEqual(ActivityLog._meta.verbose_name_plural, 'Activity Logs')
    
    def test_activity_log_indexes(self):
        """Test ActivityLog has proper database indexes"""
        indexes = ActivityLog._meta.indexes
        index_fields = [list(index.fields) for index in indexes]
        
        # Check for expected indexes
        self.assertIn(['action_type'], index_fields)
        self.assertIn(['timestamp'], index_fields)
        self.assertIn(['user'], index_fields)
        self.assertIn(['entity_type', 'entity_id'], index_fields)
    
    def test_activity_log_foreign_key_constraints(self):
        """Test ActivityLog foreign key relationships and constraints"""
        log = ActivityLog.objects.create(
            user=self.user,
            office=self.office,
            action_type='test'
        )
        
        # Test user relationship
        self.assertEqual(log.user, self.user)
        self.assertIn(log, self.user.activity_logs.all())
        
        # Test office relationship
        self.assertEqual(log.office, self.office)
        self.assertIn(log, self.office.activity_logs.all())
    
    def test_activity_log_cascade_behavior(self):
        """Test ActivityLog behavior when related objects are deleted"""
        log = ActivityLog.objects.create(
            user=self.user,
            office=self.office,
            action_type='test'
        )
        
        log_id = log.id
        
        # Delete user - log should remain but user should be NULL
        self.user.delete()
        log.refresh_from_db()
        self.assertIsNone(log.user)
        
        # Delete office - log should remain but office should be NULL
        self.office.delete()
        log.refresh_from_db()
        self.assertIsNone(log.office)
        
        # Log itself should still exist
        self.assertTrue(ActivityLog.objects.filter(id=log_id).exists())
    
    def test_activity_log_helper_method_basic(self):
        """Test ActivityLog.log_activity helper method basic functionality"""
        log = ActivityLog.log_activity(
            user=self.user,
            action_type='create',
            entity_type='person',
            entity_id=self.person.id
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'create')
        self.assertEqual(log.entity_type, 'person')
        self.assertEqual(log.entity_id, self.person.id)
    
    def test_activity_log_helper_method_with_content_object(self):
        """Test ActivityLog.log_activity with content object"""
        log = ActivityLog.log_activity(
            user=self.user,
            action_type='view',
            content_object=self.person
        )
        
        self.assertEqual(log.entity_type, 'person')
        self.assertEqual(log.entity_id, self.person.id)
    
    def test_activity_log_helper_method_with_description(self):
        """Test ActivityLog.log_activity with description text"""
        log = ActivityLog.log_activity(
            user=self.user,
            action_type='update',
            content_object=self.person,
            description_text='Updated person details'
        )
        
        self.assertEqual(log.details['message'], 'Updated person details')
    
    def test_activity_log_helper_method_with_details(self):
        """Test ActivityLog.log_activity with custom details"""
        custom_details = {'ip': '127.0.0.1', 'browser': 'Chrome'}
        
        log = ActivityLog.log_activity(
            user=self.user,
            action_type='login',
            details=custom_details,
            description_text='User logged in'
        )
        
        self.assertEqual(log.details['ip'], '127.0.0.1')
        self.assertEqual(log.details['browser'], 'Chrome')
        self.assertEqual(log.details['message'], 'User logged in')
    
    def test_activity_log_ip_address_validation(self):
        """Test ActivityLog IP address field validation"""
        # Valid IPv4
        log = ActivityLog.objects.create(
            action_type='test',
            ip_address='192.168.1.1'
        )
        self.assertEqual(log.ip_address, '192.168.1.1')
        
        # Valid IPv6
        log = ActivityLog.objects.create(
            action_type='test',
            ip_address='2001:db8::1'
        )
        self.assertEqual(log.ip_address, '2001:db8::1')
    
    def test_activity_log_timestamp_auto_set(self):
        """Test that timestamp is automatically set on creation"""
        from django.utils import timezone
        
        before_creation = timezone.now()
        
        log = ActivityLog.objects.create(action_type='test')
        
        after_creation = timezone.now()
        
        self.assertGreaterEqual(log.timestamp, before_creation)
        self.assertLessEqual(log.timestamp, after_creation)