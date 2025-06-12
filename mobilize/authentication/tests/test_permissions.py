"""
Tests for authentication permissions and decorators
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from mobilize.authentication.decorators import role_required, office_admin_required, super_admin_required

User = get_user_model()


class PermissionSystemTests(TestCase):
    """Test cases for the permission system"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create test users with different roles
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
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            role='standard_user'
        )
    
    def test_user_role_hierarchy(self):
        """Test that user roles have correct hierarchy"""
        # Test role values
        self.assertEqual(self.super_admin.role, 'super_admin')
        self.assertEqual(self.office_admin.role, 'office_admin')
        self.assertEqual(self.regular_user.role, 'standard_user')
    
    def test_user_authentication_status(self):
        """Test user authentication and properties"""
        # All created users should be authenticated when attached to request
        self.assertTrue(self.super_admin.is_authenticated)
        self.assertTrue(self.office_admin.is_authenticated)
        self.assertTrue(self.regular_user.is_authenticated)
        
        # Check user permissions
        self.assertFalse(self.regular_user.is_staff)
        self.assertFalse(self.regular_user.is_superuser)
    
    def test_anonymous_user_properties(self):
        """Test anonymous user has no special permissions"""
        anonymous = AnonymousUser()
        self.assertFalse(anonymous.is_authenticated)
        self.assertFalse(anonymous.is_staff)
        self.assertFalse(anonymous.is_superuser)


class RoleRequiredDecoratorTests(TestCase):
    """Test cases for role_required decorator"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            role='office_admin'
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            role='standard_user'
        )
    
    def test_role_required_decorator_success(self):
        """Test role_required decorator allows access for correct role"""
        
        @role_required('office_admin')
        def test_view(request):
            return HttpResponse("Success")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_role_required_decorator_forbidden(self):
        """Test role_required decorator denies access for insufficient role"""
        
        @role_required('super_admin')
        def test_view(request):
            return HttpResponse("Success")
        
        request = self.factory.get('/test/')
        request.user = self.regular_user
        
        response = test_view(request)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_role_required_decorator_anonymous(self):
        """Test role_required decorator denies access for anonymous users"""
        
        @role_required('standard_user')
        def test_view(request):
            return HttpResponse("Success")
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        response = test_view(request)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_role_hierarchy_enforcement(self):
        """Test that role hierarchy is properly enforced"""
        
        # Create additional users for this test
        super_admin = User.objects.create_user(
            username='superadmin2',
            email='super2@example.com',
            role='super_admin'
        )
        
        office_admin = User.objects.create_user(
            username='officeadmin2',
            email='office2@example.com',
            role='office_admin'
        )
        
        @role_required('standard_user')
        def test_view(request):
            return HttpResponse("Success")
        
        # Super admin should have access to standard_user required view
        request = self.factory.get('/test/')
        request.user = super_admin
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Office admin should have access to standard_user required view  
        request.user = office_admin
        response = test_view(request)
        self.assertEqual(response.status_code, 200)


class OfficeAdminDecoratorTests(TestCase):
    """Test cases for office_admin_required decorator"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            role='office_admin'
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            role='standard_user'
        )
    
    def test_office_admin_decorator_success(self):
        """Test office_admin_required decorator allows access for admin"""
        
        @office_admin_required
        def test_view(request):
            return HttpResponse("Success")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Success")
    
    def test_office_admin_decorator_forbidden(self):
        """Test office_admin_required decorator denies access for regular user"""
        
        @office_admin_required
        def test_view(request):
            return HttpResponse("Success")
        
        request = self.factory.get('/test/')
        request.user = self.regular_user
        
        response = test_view(request)
        # Should return 403
        self.assertEqual(response.status_code, 403)
    
    def test_super_admin_decorator_success(self):
        """Test super_admin_required decorator"""
        super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            role='super_admin'
        )
        
        @super_admin_required
        def test_view(request):
            return HttpResponse("Success")
        
        request = self.factory.get('/test/')
        request.user = super_admin
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)