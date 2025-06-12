"""
Tests for core models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from mobilize.core.models import ActivityLog
from mobilize.admin_panel.models import Office
from mobilize.contacts.models import Person

User = get_user_model()


class ActivityLogTests(TestCase):
    """Test cases for ActivityLog model"""
    
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
            people_user_id=str(self.user.id)
        )
    
    def test_create_activity_log(self):
        """Test creating an activity log"""
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='create',
            entity_type='person',
            entity_id=self.person.pk,
            office=self.office,
            details={'message': 'Created new person'}
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'create')
        self.assertEqual(log.entity_type, 'person')
        self.assertEqual(log.entity_id, self.person.pk)
        self.assertEqual(log.office, self.office)
        self.assertEqual(log.details['message'], 'Created new person')
        self.assertIsNotNone(log.timestamp)
    
    def test_activity_log_string_representation(self):
        """Test activity log string representation"""
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='view',
            entity_type='person',
            entity_id=self.person.pk
        )
        
        expected_parts = [
            self.user.get_full_name() or self.user.email,
            'View',
            'person',
            str(self.person.pk)
        ]
        
        str_repr = str(log)
        for part in expected_parts:
            self.assertIn(part, str_repr)
    
    def test_activity_log_action_choices(self):
        """Test different action type choices"""
        actions = ['create', 'update', 'delete', 'view', 'login', 'logout', 'export', 'import', 'sync', 'email', 'other']
        
        for action in actions:
            log = ActivityLog.objects.create(
                user=self.user,
                action_type=action,
                entity_type='test',
                entity_id=1
            )
            self.assertEqual(log.action_type, action)
    
    def test_activity_log_helper_method(self):
        """Test the log_activity helper method"""
        log = ActivityLog.log_activity(
            user=self.user,
            action_type='create',
            content_object=self.person,
            details={'ip': '127.0.0.1'},
            office=self.office,
            description_text='Created new person record'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_type, 'create')
        self.assertEqual(log.entity_type, 'person')
        self.assertEqual(log.entity_id, self.person.pk)
        self.assertEqual(log.office, self.office)
        self.assertEqual(log.details['message'], 'Created new person record')
        self.assertEqual(log.details['ip'], '127.0.0.1')
    
    def test_activity_log_without_user(self):
        """Test activity log for system actions"""
        log = ActivityLog.objects.create(
            action_type='sync',
            entity_type='system',
            details={'source': 'supabase'}
        )
        
        self.assertIsNone(log.user)
        self.assertEqual(log.action_type, 'sync')
        self.assertEqual(log.entity_type, 'system')
        
        # String representation should show 'System' for null user
        str_repr = str(log)
        self.assertIn('System', str_repr)
    
    def test_activity_log_with_ip_and_user_agent(self):
        """Test activity log with IP address and user agent"""
        log = ActivityLog.objects.create(
            user=self.user,
            action_type='login',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 Chrome/91.0'
        )
        
        self.assertEqual(log.ip_address, '192.168.1.1')
        self.assertEqual(log.user_agent, 'Mozilla/5.0 Chrome/91.0')
    
    def test_activity_log_ordering(self):
        """Test that activity logs are ordered by timestamp descending"""
        log1 = ActivityLog.objects.create(
            user=self.user,
            action_type='create',
            entity_type='test1'
        )
        
        log2 = ActivityLog.objects.create(
            user=self.user,
            action_type='create',
            entity_type='test2'
        )
        
        logs = ActivityLog.objects.all()
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)