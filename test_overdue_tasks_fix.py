#!/usr/bin/env python3
"""
Test script to verify the overdue tasks fix.
This script will test the dashboard link and task list filtering.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobilize.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from mobilize.tasks.models import Task
from mobilize.admin_panel.models import Office
from mobilize.authentication.models import UserOffice

User = get_user_model()

def test_overdue_tasks_filtering():
    """Test that overdue tasks filtering works correctly between dashboard and task list."""
    
    print("Setting up test data...")
    
    # Create test office
    office = Office.objects.create(
        name="Test Office",
        address="123 Test St"
    )
    
    # Create test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role='standard_user'
    )
    
    # Assign user to office
    UserOffice.objects.create(user=user, office=office)
    
    # Create test tasks
    today = date.today()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    
    # Create overdue tasks (should appear in overdue filter)
    overdue_pending = Task.objects.create(
        title="Overdue Pending Task",
        status="pending",
        due_date=yesterday,
        created_by=user,
        assigned_to=user,
        office=office
    )
    
    overdue_in_progress = Task.objects.create(
        title="Overdue In Progress Task", 
        status="in_progress",
        due_date=last_week,
        created_by=user,
        assigned_to=user,
        office=office
    )
    
    # Create non-overdue tasks (should NOT appear in overdue filter)
    completed_overdue = Task.objects.create(
        title="Completed Overdue Task",
        status="completed",
        due_date=yesterday,
        created_by=user,
        assigned_to=user,
        office=office,
        completed_at=timezone.now()
    )
    
    future_task = Task.objects.create(
        title="Future Task",
        status="pending", 
        due_date=today + timedelta(days=1),
        created_by=user,
        assigned_to=user,
        office=office
    )
    
    print(f"Created {Task.objects.count()} test tasks")
    
    # Test dashboard overdue count
    client = Client()
    client.login(username='testuser', password='testpass123')
    
    print("\nTesting dashboard overdue count...")
    dashboard_response = client.get(reverse('core:dashboard'))
    assert dashboard_response.status_code == 200
    
    overdue_count = dashboard_response.context['overdue_tasks']
    print(f"Dashboard shows {overdue_count} overdue tasks")
    
    # Test task list with overdue filter
    print("\nTesting task list with overdue filter...")
    task_list_response = client.get(reverse('tasks:task_list') + '?due=overdue')
    assert task_list_response.status_code == 200
    
    filtered_tasks = task_list_response.context['tasks']
    filtered_count = len(filtered_tasks)
    print(f"Task list shows {filtered_count} overdue tasks")
    
    # Verify the counts match
    assert overdue_count == filtered_count, f"Dashboard count ({overdue_count}) doesn't match task list count ({filtered_count})"
    
    # Verify the correct tasks are shown
    task_titles = [task.title for task in filtered_tasks]
    print(f"Overdue tasks found: {task_titles}")
    
    assert "Overdue Pending Task" in task_titles
    assert "Overdue In Progress Task" in task_titles
    assert "Completed Overdue Task" not in task_titles
    assert "Future Task" not in task_titles
    
    print("\n✅ All tests passed! The overdue tasks fix is working correctly.")
    
    # Cleanup
    Task.objects.all().delete()
    UserOffice.objects.all().delete()
    User.objects.filter(username='testuser').delete()
    Office.objects.filter(name='Test Office').delete()
    
    print("Test data cleaned up.")

if __name__ == '__main__':
    test_overdue_tasks_filtering()