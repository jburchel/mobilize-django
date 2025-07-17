"""
Tests for authentication models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from mobilize.authentication.models import Role, Permission, RolePermission

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Test cases for the custom User model"""

    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "role": "standard_user",
        }

    def test_create_user(self):
        """Test creating a new user"""
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertEqual(user.role, "standard_user")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        # Default role is standard_user, need to set super_admin explicitly
        user.role = "super_admin"
        user.save()
        self.assertEqual(user.role, "super_admin")

    def test_user_string_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        # Default User model string representation is just username
        expected = "testuser"
        self.assertEqual(str(user), expected)

    def test_get_full_name(self):
        """Test get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), "Test User")

    def test_role_choices(self):
        """Test that role field accepts valid choices"""
        valid_roles = ["standard_user", "limited_user", "office_admin", "super_admin"]

        for role in valid_roles:
            user_data = self.user_data.copy()
            user_data["username"] = f"test_{role}"
            user_data["email"] = f"test_{role}@example.com"
            user_data["role"] = role

            user = User.objects.create_user(**user_data)
            self.assertEqual(user.role, role)


class RoleModelTests(TestCase):
    """Test cases for the Role model"""

    def test_create_role(self):
        """Test creating a new role"""
        role = Role.objects.create(
            name="test_role", description="Test role description"
        )

        self.assertEqual(role.name, "test_role")
        self.assertEqual(role.description, "Test role description")
        self.assertEqual(str(role), "test_role")

    def test_role_unique_name(self):
        """Test that role names must be unique"""
        Role.objects.create(name="unique_role", description="First")

        with self.assertRaises(Exception):
            Role.objects.create(name="unique_role", description="Second")


class PermissionModelTests(TestCase):
    """Test cases for the Permission model"""

    def test_create_permission(self):
        """Test creating a new permission"""
        permission = Permission.objects.create(
            name="test_permission", description="Test permission description"
        )

        self.assertEqual(permission.name, "test_permission")
        self.assertEqual(permission.description, "Test permission description")
        self.assertIsNotNone(permission.created_at)
        self.assertIsNotNone(permission.updated_at)
        self.assertEqual(str(permission), "test_permission")


class RolePermissionModelTests(TestCase):
    """Test cases for the RolePermission model"""

    def setUp(self):
        self.role = Role.objects.create(name="test_role", description="Test role")
        self.permission = Permission.objects.create(
            name="test_permission", description="Test permission"
        )

    def test_create_role_permission(self):
        """Test creating a role-permission relationship"""
        role_permission = RolePermission.objects.create(
            role=self.role, permission=self.permission
        )

        self.assertEqual(role_permission.role, self.role)
        self.assertEqual(role_permission.permission, self.permission)
        self.assertEqual(
            str(role_permission), f"{self.role.name} - {self.permission.name}"
        )

    def test_unique_role_permission(self):
        """Test that role-permission combinations must be unique"""
        RolePermission.objects.create(role=self.role, permission=self.permission)

        with self.assertRaises(Exception):
            RolePermission.objects.create(role=self.role, permission=self.permission)
