"""
Tests for core permissions functionality
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from mobilize.core.permissions import DataAccessManager, get_data_access_manager, require_role
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.admin_panel.models import Office, UserOffice
from mobilize.tasks.models import Task
from mobilize.communications.models import Communication

User = get_user_model()


class DataAccessManagerTests(TestCase):
    """Test cases for DataAccessManager"""
    
    def setUp(self):
        # Create offices
        self.office1 = Office.objects.create(name='Office 1', code='OFF1')
        self.office2 = Office.objects.create(name='Office 2', code='OFF2')
        
        # Create users with different roles
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            role='super_admin'
        )
        
        self.office_admin = User.objects.create_user(
            username='officeadmin',
            email='office@example.com',
            role='office_admin'
        )
        
        self.standard_user = User.objects.create_user(
            username='standarduser',
            email='standard@example.com',
            role='standard_user'
        )
        
        self.limited_user = User.objects.create_user(
            username='limiteduser',
            email='limited@example.com',
            role='limited_user'
        )
        
        # Create user-office relationships
        UserOffice.objects.create(
            user_id=str(self.office_admin.id),
            office_id=self.office1.id
        )
        UserOffice.objects.create(
            user_id=str(self.standard_user.id),
            office_id=self.office1.id
        )
        
        # Create test people
        self.person1 = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            assigned_to=str(self.office_admin.id),
            user_id=self.office1.id
        )
        
        self.person2 = Person.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            assigned_to=str(self.standard_user.id),
            user_id=self.office2.id
        )
        
        # Create test churches
        self.church1 = Church.objects.create(
            name='Test Church 1',
            denomination='Baptist',
            office_id=self.office1.id
        )
        
        self.church2 = Church.objects.create(
            name='Test Church 2',
            denomination='Methodist',
            office_id=self.office2.id
        )
    
    def test_super_admin_can_view_all_people(self):
        """Test that super admin can view all people"""
        manager = DataAccessManager(self.super_admin)
        queryset = manager.get_people_queryset()
        
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.person1, queryset)
        self.assertIn(self.person2, queryset)
    
    def test_super_admin_my_only_view(self):
        """Test super admin viewing only their assigned people"""
        manager = DataAccessManager(self.super_admin, view_mode='my_only')
        queryset = manager.get_people_queryset()
        
        # Should only see people assigned to them
        assigned_count = queryset.filter(assigned_to=str(self.super_admin.id)).count()
        self.assertEqual(queryset.count(), assigned_count)
    
    def test_office_admin_can_view_office_people(self):
        """Test that office admin can view people in their office"""
        manager = DataAccessManager(self.office_admin)
        queryset = manager.get_people_queryset()
        
        # Should see people in their office or assigned to them
        self.assertGreaterEqual(queryset.count(), 1)
    
    def test_office_admin_my_only_view(self):
        """Test office admin viewing only their assigned people"""
        manager = DataAccessManager(self.office_admin, view_mode='my_only')
        queryset = manager.get_people_queryset()
        
        # Should only see people assigned to them
        for person in queryset:
            self.assertEqual(person.assigned_to, str(self.office_admin.id))
    
    def test_standard_user_can_only_view_assigned_people(self):
        """Test that standard user can only view their assigned people"""
        manager = DataAccessManager(self.standard_user)
        queryset = manager.get_people_queryset()
        
        # Should only see people assigned to them
        for person in queryset:
            self.assertEqual(person.assigned_to, str(self.standard_user.id))
    
    def test_super_admin_can_view_all_churches(self):
        """Test that super admin can view all churches"""
        manager = DataAccessManager(self.super_admin)
        queryset = manager.get_churches_queryset()
        
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.church1, queryset)
        self.assertIn(self.church2, queryset)
    
    def test_office_admin_can_view_office_churches(self):
        """Test that office admin can view churches in their office"""
        manager = DataAccessManager(self.office_admin)
        queryset = manager.get_churches_queryset()
        
        # Should see churches in their office
        office_churches = queryset.filter(office_id=self.office1.id)
        self.assertGreater(office_churches.count(), 0)
    
    def test_can_view_all_data_permissions(self):
        """Test can_view_all_data method"""
        super_admin_manager = DataAccessManager(self.super_admin)
        office_admin_manager = DataAccessManager(self.office_admin)
        standard_user_manager = DataAccessManager(self.standard_user)
        
        self.assertTrue(super_admin_manager.can_view_all_data())
        self.assertTrue(office_admin_manager.can_view_all_data())
        self.assertFalse(standard_user_manager.can_view_all_data())
    
    def test_get_view_mode_display(self):
        """Test view mode display text"""
        super_admin_manager = DataAccessManager(self.super_admin, 'default')
        super_admin_my_manager = DataAccessManager(self.super_admin, 'my_only')
        office_admin_manager = DataAccessManager(self.office_admin, 'default')
        standard_user_manager = DataAccessManager(self.standard_user)
        
        self.assertEqual(super_admin_manager.get_view_mode_display(), "All Offices")
        self.assertEqual(super_admin_my_manager.get_view_mode_display(), "My Contacts Only")
        self.assertEqual(office_admin_manager.get_view_mode_display(), "My Office")
        self.assertEqual(standard_user_manager.get_view_mode_display(), "My Contacts")


class DataAccessManagerFactoryTests(TestCase):
    """Test cases for data access manager factory function"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='standard_user'
        )
    
    def test_get_data_access_manager_default(self):
        """Test creating data access manager with default view mode"""
        request = self.factory.get('/')
        request.user = self.user
        
        manager = get_data_access_manager(request)
        
        self.assertEqual(manager.user, self.user)
        self.assertEqual(manager.view_mode, 'default')
    
    def test_get_data_access_manager_with_view_mode(self):
        """Test creating data access manager with specific view mode"""
        request = self.factory.get('/?view_mode=my_only')
        request.user = self.user
        
        manager = get_data_access_manager(request)
        
        self.assertEqual(manager.user, self.user)
        self.assertEqual(manager.view_mode, 'my_only')


class RequireRoleDecoratorTests(TestCase):
    """Test cases for require_role decorator"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            role='super_admin'
        )
        
        self.standard_user = User.objects.create_user(
            username='standard',
            email='standard@example.com',
            role='standard_user'
        )
        
        self.user_no_role = User.objects.create_user(
            username='norole',
            email='norole@example.com'
        )
    
    def test_require_role_allows_correct_role(self):
        """Test that decorator allows users with correct role"""
        @require_role(['super_admin'])
        def test_view(request):
            return "Success"
        
        request = self.factory.get('/')
        request.user = self.admin_user
        
        result = test_view(request)
        self.assertEqual(result, "Success")
    
    def test_require_role_blocks_incorrect_role(self):
        """Test that decorator blocks users with incorrect role"""
        @require_role(['super_admin'])
        def test_view(request):
            return "Success"
        
        request = self.factory.get('/')
        request.user = self.standard_user
        
        result = test_view(request)
        self.assertEqual(result.status_code, 403)
    
    def test_require_role_blocks_user_without_role(self):
        """Test that decorator blocks users without role attribute"""
        @require_role(['super_admin'])
        def test_view(request):
            return "Success"
        
        request = self.factory.get('/')
        request.user = self.user_no_role
        
        result = test_view(request)
        self.assertEqual(result.status_code, 403)
    
    def test_require_role_allows_multiple_roles(self):
        """Test that decorator works with multiple allowed roles"""
        @require_role(['super_admin', 'office_admin'])
        def test_view(request):
            return "Success"
        
        request = self.factory.get('/')
        request.user = self.admin_user
        
        result = test_view(request)
        self.assertEqual(result, "Success")