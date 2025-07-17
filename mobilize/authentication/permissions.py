"""
Permission models for the authentication system.

This module contains models for roles and permissions that integrate
with Django's auth system and match the Supabase schema.
"""

from django.db import models
from django.utils import timezone


class Role(models.Model):
    """
    Role model for defining user roles.

    Matches the 'roles' table in the Supabase database.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    Permission model for defining system permissions.

    Matches the 'permissions' table in the Supabase database.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "permissions"
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ["name"]

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """
    Junction model for mapping permissions to roles.

    Matches the 'role-permissions' table in the Supabase database.
    """

    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "role_permissions"
        unique_together = ("role", "permission")
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["permission"]),
        ]

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"
