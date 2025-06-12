"""
Tests for admin_panel views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from mobilize.admin_panel.models import Office, UserOffice

User = get_user_model()


class AdminPanelViewTests(TestCase):
    """Test cases for admin panel views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create users with different roles
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='superpass123',
            role='super_admin'
        )
        
        self.office_admin = User.objects.create_user(
            username='officeadmin',
            email='office@example.com',
            password='officepass123',
            role='office_admin'
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123',
            role='standard_user'
        )
        
        # Create test office
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST001',
            city='Test City'
        )
        
        # Assign office admin to office
        UserOffice.objects.create(
            user=self.office_admin,
            office=self.office,
            role='office_admin'
        )
    
    def test_admin_panel_allows_authenticated_users(self):
        """Test that admin panel allows authenticated users to view office list"""
        # Test with regular user - they can see office list but only their offices
        self.client.login(username='user', password='userpass123')
        url = reverse('admin_panel:office_list')
        response = self.client.get(url)
        
        # Should allow access but show empty list (no offices assigned)
        self.assertEqual(response.status_code, 200)
    
    def test_admin_panel_super_admin_access(self):
        """Test that super admin can access admin panel"""
        self.client.login(username='superadmin', password='superpass123')
        url = reverse('admin_panel:office_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Offices')
    
    def test_admin_panel_office_admin_access(self):
        """Test that office admin can access admin panel"""
        self.client.login(username='officeadmin', password='officepass123')
        url = reverse('admin_panel:office_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Offices')


class OfficeViewTests(TestCase):
    """Test cases for office management views"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='office_admin'
        )
        
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST001',
            city='Test City',
            phone='+1234567890'
        )
    
    def test_office_list_view(self):
        """Test office list view"""
        # Need to assign admin user to the office first
        UserOffice.objects.create(
            user=self.admin_user,
            office=self.office,
            role='office_admin'
        )
        
        self.client.login(username='admin', password='adminpass123')
        url = reverse('admin_panel:office_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.office.name)
        self.assertContains(response, self.office.code)
    
    def test_office_detail_view(self):
        """Test office detail view"""
        # Need to assign admin user to the office first  
        UserOffice.objects.create(
            user=self.admin_user,
            office=self.office,
            role='office_admin'
        )
        
        self.client.login(username='admin', password='adminpass123')
        url = reverse('admin_panel:office_detail', kwargs={'pk': self.office.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.office.name)
        self.assertContains(response, self.office.city)
        self.assertContains(response, self.office.phone)
    
    def test_office_create_view_get_super_admin(self):
        """Test office creation form for super admin"""
        # Create super admin user
        super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='superpass123',
            role='super_admin'
        )
        
        self.client.login(username='superadmin', password='superpass123')
        url = reverse('admin_panel:office_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check form fields are present
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="code"')
    
    def test_office_create_view_post_super_admin(self):
        """Test office creation via POST for super admin"""
        # Create super admin user
        super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='superpass123',
            role='super_admin'
        )
        
        self.client.login(username='superadmin', password='superpass123')
        url = reverse('admin_panel:office_create')
        
        office_data = {
            'name': 'New Office',
            'code': 'NEW001',
            'address': '456 New Street',
            'city': 'New City',
            'state': 'New State',
            'country': 'New Country',
            'postal_code': '67890',
            'phone': '+0987654321',
            'email': 'new@office.com',
            'timezone_name': 'America/Los_Angeles'
        }
        
        response = self.client.post(url, office_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check office was created
        new_office = Office.objects.filter(name='New Office').first()
        self.assertIsNotNone(new_office)
        self.assertEqual(new_office.code, 'NEW001')
        self.assertEqual(new_office.city, 'New City')
    
    def test_office_update_view_get(self):
        """Test office update form"""
        # Create super admin user
        super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='superpass123',
            role='super_admin'
        )
        
        self.client.login(username='superadmin', password='superpass123')
        url = reverse('admin_panel:office_update', kwargs={'pk': self.office.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.office.name)
    
    def test_office_update_view_post(self):
        """Test office update via POST"""
        # Create super admin user
        super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='superpass123',
            role='super_admin'
        )
        
        self.client.login(username='superadmin', password='superpass123')
        url = reverse('admin_panel:office_update', kwargs={'pk': self.office.pk})
        
        updated_data = {
            'name': 'Updated Office Name',
            'code': self.office.code,  # Keep same code
            'address': 'Updated Address',
            'city': 'Updated City',
            'state': 'Updated State',
            'phone': self.office.phone,
            'timezone_name': 'America/Chicago',
            'is_active': True  # Include required field
        }
        
        response = self.client.post(url, updated_data)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check office was updated
        self.office.refresh_from_db()
        self.assertEqual(self.office.name, 'Updated Office Name')
        self.assertEqual(self.office.city, 'Updated City')
        self.assertEqual(self.office.timezone_name, 'America/Chicago')
    
    def test_office_delete_view(self):
        """Test office deletion"""
        # Create super admin user
        super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='superpass123',
            role='super_admin'
        )
        
        self.client.login(username='superadmin', password='superpass123')
        url = reverse('admin_panel:office_delete', kwargs={'pk': self.office.pk})
        
        # Test GET (confirmation page)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.office.name)
        
        # Test POST (actual deletion)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Check office was deleted
        self.assertFalse(Office.objects.filter(pk=self.office.pk).exists())


class UserOfficeManagementTests(TestCase):
    """Test cases for user-office management"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='office_admin'
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123',
            role='standard_user'
        )
        
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST001'
        )
        
        self.user_office = UserOffice.objects.create(
            user=self.regular_user,
            office=self.office,
            role='standard_user'
        )
    
    def test_user_office_list_view(self):
        """Test listing users in an office"""
        self.client.login(username='admin', password='adminpass123')
        url = reverse('admin_panel:office_users', kwargs={'office_id': self.office.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.regular_user.username)
        self.assertContains(response, 'standard_user')
    
    def test_add_user_to_office(self):
        """Test adding a user to an office"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            role='standard_user'
        )
        
        # Need to assign admin user to the office first
        UserOffice.objects.create(
            user=self.admin_user,
            office=self.office,
            role='office_admin'
        )
        
        self.client.login(username='admin', password='adminpass123')
        url = reverse('admin_panel:add_user_to_office', kwargs={'office_id': self.office.pk})
        
        data = {
            'user_id': new_user.pk,
            'role': 'standard_user'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful addition
        self.assertEqual(response.status_code, 302)
        
        # Check user was added to office
        user_office = UserOffice.objects.filter(
            user=new_user,
            office=self.office
        ).first()
        
        self.assertIsNotNone(user_office)
        self.assertEqual(user_office.role, 'standard_user')
    
    def test_remove_user_from_office(self):
        """Test removing a user from an office"""
        # Need to assign admin user to the office first
        UserOffice.objects.create(
            user=self.admin_user,
            office=self.office,
            role='office_admin'
        )
        
        self.client.login(username='admin', password='adminpass123')
        url = reverse('admin_panel:remove_user_from_office', kwargs={
            'office_id': self.office.pk,
            'user_id': self.regular_user.pk
        })
        
        response = self.client.post(url)
        
        # Should redirect after successful removal
        self.assertEqual(response.status_code, 302)
        
        # Check user was removed from office
        user_office_exists = UserOffice.objects.filter(
            user=self.regular_user,
            office=self.office
        ).exists()
        
        self.assertFalse(user_office_exists)
    
    def test_change_user_role_in_office(self):
        """Test changing a user's role in an office"""
        # Need to assign admin user to the office first
        UserOffice.objects.create(
            user=self.admin_user,
            office=self.office,
            role='office_admin'
        )
        
        self.client.login(username='admin', password='adminpass123')
        url = reverse('admin_panel:update_user_office_role', kwargs={
            'office_id': self.office.pk,
            'user_id': self.regular_user.pk
        })
        
        data = {'role': 'office_admin'}
        response = self.client.post(url, data)
        
        # Should redirect after successful role change
        self.assertEqual(response.status_code, 302)
        
        # Check role was updated
        self.user_office.refresh_from_db()
        self.assertEqual(self.user_office.role, 'office_admin')