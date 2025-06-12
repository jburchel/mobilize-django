"""
Tests for tasks views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from mobilize.tasks.models import Task
from mobilize.contacts.models import Person

User = get_user_model()


class TaskViewTests(TestCase):
    """Test cases for task views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123',
            role='user'
        )
        
        # Create test tasks
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            status='pending',
            priority='medium',
            due_date=timezone.now() + timedelta(days=7),
            assigned_to=self.user,
            created_by=self.user
        )
        
        self.other_task = Task.objects.create(
            title='Other User Task',
            description='Other user description',
            status='pending',
            priority='high',
            due_date=timezone.now() + timedelta(days=3),
            assigned_to=self.other_user,
            created_by=self.other_user
        )
    
    def test_task_list_requires_login(self):
        """Test that task list requires authentication"""
        url = reverse('tasks:task_list')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_task_list_view_authenticated(self):
        """Test task list view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tasks')
        self.assertContains(response, self.task.title)
        
        # Should not see other user's tasks
        self.assertNotContains(response, self.other_task.title)
    
    def test_task_detail_view(self):
        """Test task detail view"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_detail', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertContains(response, self.task.description)
    
    def test_task_detail_access_control(self):
        """Test that users can only access their own tasks"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_detail', kwargs={'pk': self.other_task.pk})
        response = self.client.get(url)
        
        # Should return 404 or 403
        self.assertIn(response.status_code, [403, 404])
    
    def test_task_create_view_get(self):
        """Test task creation form"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Task')
        
        # Check form fields are present
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'name="priority"')
        self.assertContains(response, 'name="due_date"')
    
    def test_task_create_view_post(self):
        """Test task creation via POST"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_create')
        
        task_data = {
            'title': 'New Task',
            'description': 'New task description',
            'priority': 'high',
            'due_date': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%d %H:%M'),
            'status': 'pending'
        }
        
        response = self.client.post(url, task_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check task was created
        new_task = Task.objects.filter(title='New Task').first()
        self.assertIsNotNone(new_task)
        self.assertEqual(new_task.assigned_to, self.user)
        self.assertEqual(new_task.created_by, self.user)
    
    def test_task_update_view_get(self):
        """Test task update form"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_edit', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Task')
        self.assertContains(response, self.task.title)
    
    def test_task_update_view_post(self):
        """Test task update via POST"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_edit', kwargs={'pk': self.task.pk})
        
        updated_data = {
            'title': 'Updated Task Title',
            'description': self.task.description,
            'priority': 'high',
            'due_date': self.task.due_date.strftime('%Y-%m-%d %H:%M'),
            'status': 'in_progress'
        }
        
        response = self.client.post(url, updated_data)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check task was updated
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task Title')
        self.assertEqual(self.task.status, 'in_progress')
        self.assertEqual(self.task.priority, 'high')
    
    def test_task_delete_view(self):
        """Test task deletion"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_delete', kwargs={'pk': self.task.pk})
        
        # Test GET (confirmation page)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Task')
        self.assertContains(response, self.task.title)
        
        # Test POST (actual deletion)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Check task was deleted
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
    
    def test_task_complete_action(self):
        """Test marking task as complete"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_complete', kwargs={'pk': self.task.pk})
        
        response = self.client.post(url)
        
        # Should redirect after completion
        self.assertEqual(response.status_code, 302)
        
        # Check task status was updated
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')
        self.assertIsNotNone(self.task.completed_at)
    
    def test_task_filter_by_status(self):
        """Test filtering tasks by status"""
        # Create completed task
        completed_task = Task.objects.create(
            title='Completed Task',
            status='completed',
            priority='low',
            assigned_to=self.user,
            created_by=self.user
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Test filter by pending
        url = reverse('tasks:task_list') + '?status=pending'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertNotContains(response, completed_task.title)
        
        # Test filter by completed
        url = reverse('tasks:task_list') + '?status=completed'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, completed_task.title)
        self.assertNotContains(response, self.task.title)
    
    def test_task_filter_by_priority(self):
        """Test filtering tasks by priority"""
        # Create high priority task
        high_priority_task = Task.objects.create(
            title='High Priority Task',
            status='pending',
            priority='high',
            assigned_to=self.user,
            created_by=self.user
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Test filter by priority
        url = reverse('tasks:task_list') + '?priority=high'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, high_priority_task.title)
        # self.task has medium priority, so should not appear
        if self.task.priority != 'high':
            self.assertNotContains(response, self.task.title)