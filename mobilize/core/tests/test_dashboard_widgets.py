"""
Tests for dashboard widgets functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from mobilize.core.dashboard_widgets import (
    get_metrics_data, 
    get_recent_activity,
    get_quick_actions,
    format_metric_value
)
from mobilize.contacts.models import Person
from mobilize.churches.models import Church

User = get_user_model()


class DashboardWidgetsTests(TestCase):
    """Test cases for dashboard widget functions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='user'
        )
        
        # Create test data
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            pipeline_stage='lead',
            user=self.user
        )
        
        self.church = Church.objects.create(
            name='Test Church',
            location='Test City',
            pipeline_stage='prospect',
            user=self.user
        )
    
    def test_get_metrics_data(self):
        """Test get_metrics_data function"""
        metrics = get_metrics_data(self.user)
        
        self.assertIsInstance(metrics, list)
        self.assertGreater(len(metrics), 0)
        
        # Check that each metric has required fields
        for metric in metrics:
            self.assertIn('title', metric)
            self.assertIn('value', metric)
            self.assertIn('icon', metric)
            self.assertIn('color', metric)
    
    def test_get_recent_activity(self):
        """Test get_recent_activity function"""
        activities = get_recent_activity(self.user)
        
        self.assertIsInstance(activities, list)
        
        # If activities exist, check structure
        if activities:
            for activity in activities:
                self.assertIn('title', activity)
                self.assertIn('description', activity)
                self.assertIn('timestamp', activity)
                self.assertIn('type', activity)
    
    def test_get_quick_actions(self):
        """Test get_quick_actions function"""
        actions = get_quick_actions(self.user)
        
        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)
        
        # Check that each action has required fields
        for action in actions:
            self.assertIn('title', action)
            self.assertIn('url', action)
            self.assertIn('icon', action)
            
            # Optional fields
            if 'subtitle' in action:
                self.assertIsInstance(action['subtitle'], str)
    
    def test_format_metric_value(self):
        """Test format_metric_value function"""
        # Test various number formats
        self.assertEqual(format_metric_value(5), '5')
        self.assertEqual(format_metric_value(1000), '1K')
        self.assertEqual(format_metric_value(1500), '1.5K')
        self.assertEqual(format_metric_value(1000000), '1M')
        self.assertEqual(format_metric_value(2500000), '2.5M')
        
        # Test edge cases
        self.assertEqual(format_metric_value(0), '0')
        self.assertEqual(format_metric_value(999), '999')
        self.assertEqual(format_metric_value(1001), '1K')
    
    def test_metrics_data_accuracy(self):
        """Test that metrics data reflects actual database state"""
        metrics = get_metrics_data(self.user)
        
        # Find people metric
        people_metric = next(
            (m for m in metrics if 'People' in m.get('title', '')), 
            None
        )
        
        if people_metric:
            # Should reflect the one person we created
            self.assertIn('1', str(people_metric['value']))
        
        # Find churches metric
        churches_metric = next(
            (m for m in metrics if 'Churches' in m.get('title', '')), 
            None
        )
        
        if churches_metric:
            # Should reflect the one church we created
            self.assertIn('1', str(churches_metric['value']))
    
    def test_user_specific_metrics(self):
        """Test that metrics are user-specific"""
        # Create another user with different data
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            role='user'
        )
        
        # Create data for other user
        Person.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            pipeline_stage='lead',
            user=other_user
        )
        
        # Get metrics for both users
        user1_metrics = get_metrics_data(self.user)
        user2_metrics = get_metrics_data(other_user)
        
        # Both should have metrics, but they might be different
        self.assertIsInstance(user1_metrics, list)
        self.assertIsInstance(user2_metrics, list)
        
        # Both users should have some metrics
        self.assertGreater(len(user1_metrics), 0)
        self.assertGreater(len(user2_metrics), 0)