"""
Tests for admin_panel models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from mobilize.admin_panel.models import Office, UserOffice

User = get_user_model()


class OfficeModelTests(TestCase):
    """Test cases for the Office model"""
    
    def setUp(self):
        self.office_data = {
            'name': 'Test Office',
            'code': 'TEST001',
            'address': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'Test Country',
            'postal_code': '12345',
            'phone': '+1234567890',
            'email': 'office@test.com',
            'timezone_name': 'America/New_York'
        }
    
    def test_create_office(self):
        """Test creating a new office"""
        office = Office.objects.create(**self.office_data)
        
        self.assertEqual(office.name, 'Test Office')
        self.assertEqual(office.code, 'TEST001')
        self.assertEqual(office.address, '123 Test Street')
        self.assertEqual(office.city, 'Test City')
        self.assertEqual(office.state, 'Test State')
        self.assertEqual(office.country, 'Test Country')
        self.assertEqual(office.postal_code, '12345')
        self.assertEqual(office.phone, '+1234567890')
        self.assertEqual(office.email, 'office@test.com')
        self.assertEqual(office.timezone_name, 'America/New_York')
        self.assertTrue(office.is_active)
        self.assertIsNotNone(office.created_at)
        self.assertIsNotNone(office.updated_at)
    
    def test_office_string_representation(self):
        """Test office string representation"""
        office = Office.objects.create(**self.office_data)
        self.assertEqual(str(office), 'Test Office')
    
    def test_office_code_unique(self):
        """Test that office codes must be unique"""
        Office.objects.create(**self.office_data)
        
        # Try to create another office with same code
        duplicate_data = self.office_data.copy()
        duplicate_data['name'] = 'Another Office'
        
        with self.assertRaises(Exception):
            Office.objects.create(**duplicate_data)
    
    def test_office_minimal_data(self):
        """Test creating office with minimal required data"""
        minimal_office = Office.objects.create(
            name='Minimal Office',
            code='MIN001'
        )
        
        self.assertEqual(minimal_office.name, 'Minimal Office')
        self.assertEqual(minimal_office.code, 'MIN001')
        self.assertTrue(minimal_office.is_active)
        self.assertEqual(minimal_office.timezone_name, 'UTC')
    
    def test_office_settings_json(self):
        """Test office settings JSON field"""
        settings_data = {
            'theme': 'dark',
            'notifications': True,
            'default_view': 'grid',
            'features': ['calendar', 'reports', 'analytics']
        }
        
        office = Office.objects.create(
            name='Settings Office',
            code='SET001',
            settings=settings_data
        )
        
        self.assertEqual(office.settings, settings_data)
        self.assertEqual(office.settings['theme'], 'dark')
        self.assertTrue(office.settings['notifications'])
        self.assertIn('calendar', office.settings['features'])
    
    def test_office_active_status(self):
        """Test office active/inactive status"""
        office = Office.objects.create(**self.office_data)
        
        # Should be active by default
        self.assertTrue(office.is_active)
        
        # Deactivate office
        office.is_active = False
        office.save()
        
        self.assertFalse(office.is_active)


class UserOfficeModelTests(TestCase):
    """Test cases for the UserOffice model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='standard_user'
        )
        
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            role='office_admin'
        )
        
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST001'
        )
    
    def test_create_user_office_relationship(self):
        """Test creating a user-office relationship"""
        user_office = UserOffice.objects.create(
            user=self.user,
            office=self.office,
            role='standard_user'
        )
        
        self.assertEqual(user_office.user, self.user)
        self.assertEqual(user_office.office, self.office)
        self.assertEqual(user_office.role, 'standard_user')
        self.assertFalse(user_office.is_primary)
        self.assertIsNotNone(user_office.assigned_at)
    
    def test_user_office_string_representation(self):
        """Test user-office string representation"""
        user_office = UserOffice.objects.create(
            user=self.user,
            office=self.office,
            role='standard_user'
        )
        
        expected = f"{self.user.username} - {self.office.name} (Standard User)"
        self.assertEqual(str(user_office), expected)
    
    def test_user_office_role_choices(self):
        """Test user-office role choices"""
        valid_roles = ['office_admin', 'standard_user', 'limited_user']
        
        for role in valid_roles:
            # Create a unique user for each role test
            user = User.objects.create_user(
                username=f'user_{role}',
                email=f'{role}@example.com',
                role='standard_user'
            )
            
            user_office = UserOffice.objects.create(
                user=user,
                office=self.office,
                role=role
            )
            
            self.assertEqual(user_office.role, role)
    
    def test_unique_user_office_combination(self):
        """Test that user-office combinations must be unique"""
        UserOffice.objects.create(
            user=self.user,
            office=self.office,
            role='standard_user'
        )
        
        # Try to create duplicate relationship
        with self.assertRaises(Exception):
            UserOffice.objects.create(
                user=self.user,
                office=self.office,
                role='office_admin'  # Different role but same user-office
            )
    
    def test_user_multiple_offices(self):
        """Test that a user can belong to multiple offices"""
        office2 = Office.objects.create(
            name='Second Office',
            code='SEC001'
        )
        
        # Add user to first office
        user_office1 = UserOffice.objects.create(
            user=self.user,
            office=self.office,
            role='standard_user'
        )
        
        # Add same user to second office
        user_office2 = UserOffice.objects.create(
            user=self.user,
            office=office2,
            role='office_admin'
        )
        
        # Both relationships should exist
        self.assertEqual(user_office1.user, self.user)
        self.assertEqual(user_office2.user, self.user)
        self.assertEqual(user_office1.office, self.office)
        self.assertEqual(user_office2.office, office2)
        self.assertEqual(user_office1.role, 'standard_user')
        self.assertEqual(user_office2.role, 'office_admin')
    
    def test_office_multiple_users(self):
        """Test that an office can have multiple users"""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            role='standard_user'
        )
        
        # Add first user to office
        user_office1 = UserOffice.objects.create(
            user=self.user,
            office=self.office,
            role='standard_user'
        )
        
        # Add second user to same office
        user_office2 = UserOffice.objects.create(
            user=user2,
            office=self.office,
            role='office_admin'
        )
        
        # Both relationships should exist
        office_users = UserOffice.objects.filter(office=self.office)
        self.assertEqual(office_users.count(), 2)
        
        users_in_office = [uo.user for uo in office_users]
        self.assertIn(self.user, users_in_office)
        self.assertIn(user2, users_in_office)
    
    def test_user_office_primary_setting(self):
        """Test setting primary office for user"""
        user_office = UserOffice.objects.create(
            user=self.user,
            office=self.office,
            role='standard_user',
            is_primary=True
        )
        
        # Should be primary
        self.assertTrue(user_office.is_primary)
        
        # Create second office for same user
        office2 = Office.objects.create(
            name='Second Office',
            code='SEC002'
        )
        
        user_office2 = UserOffice.objects.create(
            user=self.user,
            office=office2,
            role='standard_user',
            is_primary=True
        )
        
        # First office should no longer be primary due to save() override
        user_office.refresh_from_db()
        self.assertFalse(user_office.is_primary)
        self.assertTrue(user_office2.is_primary)