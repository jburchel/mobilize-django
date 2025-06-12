"""
Tests for core views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from mobilize.core.models import DashboardPreference

User = get_user_model()


class DashboardViewTests(TestCase):
    """Test cases for dashboard views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='office_admin'
        )
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        url = reverse('core:dashboard')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('core:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Mobilize CRM')
    
    def test_dashboard_creates_preferences(self):
        """Test that dashboard creates preferences if they don't exist"""
        self.client.login(username='testuser', password='testpass123')
        
        # Ensure no preferences exist
        self.assertFalse(
            DashboardPreference.objects.filter(user=self.user).exists()
        )
        
        url = reverse('core:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Preferences should be created
        self.assertTrue(
            DashboardPreference.objects.filter(user=self.user).exists()
        )
    
    def test_dashboard_context_data(self):
        """Test dashboard view context data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('core:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that expected context variables are present
        context = response.context
        self.assertIn('metrics', context)
        self.assertIn('recent_activity', context)
        self.assertIn('quick_actions', context)
        
        # Metrics should be a list
        self.assertIsInstance(context['metrics'], list)


class ReportsViewTests(TestCase):
    """Test cases for reports views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='office_admin'
        )
    
    def test_reports_requires_login(self):
        """Test that reports require authentication"""
        url = reverse('core:reports')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_reports_view_authenticated(self):
        """Test reports view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('core:reports')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reports')
    
    def test_reports_admin_features(self):
        """Test that admin users see additional report features"""
        self.client.login(username='admin', password='adminpass123')
        url = reverse('core:reports')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Admin users should see additional options
        context = response.context
        if 'can_export_all' in context:
            self.assertTrue(context['can_export_all'])


class SettingsViewTests(TestCase):
    """Test cases for settings views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )
    
    def test_settings_requires_login(self):
        """Test that settings require authentication"""
        url = reverse('core:settings')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_settings_view_authenticated(self):
        """Test settings view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('core:settings')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings')
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('core:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile')
        self.assertContains(response, self.user.username)