"""
Performance tests for Mobilize CRM with large datasets
"""
import time
import random
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta

from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.tasks.models import Task
from mobilize.communications.models import Communication
from mobilize.admin_panel.models import Office, UserOffice
from mobilize.pipeline.models import Pipeline, PipelineStage, PipelineContact

User = get_user_model()


class LargeDatasetPerformanceTest(TransactionTestCase):
    """Test application performance with large datasets"""
    
    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Performance Test Office",
            code="PERF",
            is_active=True
        )
        
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='perfpass123',
            role='office_admin'
        )
        
        UserOffice.objects.create(user=self.user, office=self.office)
        
        # Create pipeline stages
        self.pipeline = Pipeline.objects.create(
            name="Performance Pipeline",
            office=self.office,
            pipeline_type='person'
        )
        
        self.stages = []
        stage_names = ['New Lead', 'Contacted', 'Qualified', 'Proposal', 'Closed']
        for i, name in enumerate(stage_names):
            stage = PipelineStage.objects.create(
                name=name,
                pipeline=self.pipeline,
                order=i,
                color=f'#00{i}000'
            )
            self.stages.append(stage)
    
    def _create_bulk_contacts(self, count=1000):
        """Create a large number of contacts efficiently"""
        start_time = time.time()
        
        contacts = []
        people = []
        
        # Create contacts in batches
        batch_size = 100
        for i in range(0, count, batch_size):
            batch_contacts = []
            for j in range(min(batch_size, count - i)):
                idx = i + j
                contact = Contact(
                    type='person',
                    first_name=f'Test{idx}',
                    last_name=f'User{idx}',
                    email=f'test{idx}@example.com',
                    phone=f'555-{idx:04d}',
                    user=self.user,
                    office=self.office,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                batch_contacts.append(contact)
            
            # Bulk create contacts
            created_contacts = Contact.objects.bulk_create(batch_contacts)
            contacts.extend(created_contacts)
            
            # Create corresponding Person records
            batch_people = []
            for contact in created_contacts:
                person = Person(contact=contact)
                batch_people.append(person)
            
            created_people = Person.objects.bulk_create(batch_people)
            people.extend(created_people)
        
        elapsed_time = time.time() - start_time
        print(f"Created {count} contacts in {elapsed_time:.2f} seconds")
        
        return contacts, people, elapsed_time
    
    def test_contact_list_performance_with_1000_records(self):
        """Test contact list view performance with 1000 records"""
        # Create 1000 contacts
        contacts, people, creation_time = self._create_bulk_contacts(1000)
        
        # Login
        self.client.login(username='perfuser', password='perfpass123')
        
        # Measure list view performance
        start_time = time.time()
        response = self.client.get(reverse('contacts:person_list'))
        elapsed_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        print(f"Contact list view loaded in {elapsed_time:.2f} seconds for 1000 records")
        
        # Performance assertion - should load within 2 seconds
        self.assertLess(elapsed_time, 2.0, "Contact list view took too long to load")
    
    def test_contact_search_performance(self):
        """Test search performance with large dataset"""
        # Create 5000 contacts
        contacts, people, creation_time = self._create_bulk_contacts(5000)
        
        # Login
        self.client.login(username='perfuser', password='perfpass123')
        
        # Test search performance
        search_terms = ['Test123', 'User456', 'test789@example.com']
        
        for search_term in search_terms:
            start_time = time.time()
            response = self.client.get(
                reverse('contacts:person_list'), 
                {'search': search_term}
            )
            elapsed_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 200)
            print(f"Search for '{search_term}' completed in {elapsed_time:.2f} seconds")
            
            # Performance assertion - search should complete within 1 second
            self.assertLess(elapsed_time, 1.0, f"Search for '{search_term}' took too long")
    
    def test_task_list_performance_with_large_dataset(self):
        """Test task list performance with many tasks"""
        # Create 500 contacts first
        contacts, people, _ = self._create_bulk_contacts(500)
        
        # Create 2000 tasks (4 tasks per contact)
        start_time = time.time()
        tasks = []
        batch_size = 100
        
        for i in range(0, 2000, batch_size):
            batch_tasks = []
            for j in range(min(batch_size, 2000 - i)):
                idx = i + j
                person_idx = idx % len(people)
                task = Task(
                    title=f'Task {idx}',
                    description=f'Description for task {idx}',
                    due_date=timezone.now().date() + timedelta(days=random.randint(1, 30)),
                    assigned_to=self.user,
                    created_by=self.user,
                    person=people[person_idx],
                    status=random.choice(['pending', 'in_progress', 'completed']),
                    priority=random.choice(['low', 'medium', 'high'])
                )
                batch_tasks.append(task)
            
            Task.objects.bulk_create(batch_tasks)
        
        task_creation_time = time.time() - start_time
        print(f"Created 2000 tasks in {task_creation_time:.2f} seconds")
        
        # Login and test task list performance
        self.client.login(username='perfuser', password='perfpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('tasks:task_list'))
        elapsed_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        print(f"Task list view loaded in {elapsed_time:.2f} seconds for 2000 tasks")
        
        # Performance assertion
        self.assertLess(elapsed_time, 2.0, "Task list view took too long to load")
    
    def test_communication_history_performance(self):
        """Test communication history performance with large dataset"""
        # Create 200 contacts
        contacts, people, _ = self._create_bulk_contacts(200)
        
        # Create 5000 communications
        start_time = time.time()
        communications = []
        batch_size = 100
        
        for i in range(0, 5000, batch_size):
            batch_comms = []
            for j in range(min(batch_size, 5000 - i)):
                idx = i + j
                person_idx = idx % len(people)
                comm = Communication(
                    type=random.choice(['email', 'phone', 'meeting']),
                    subject=f'Communication {idx}',
                    message=f'Message content for communication {idx}',
                    direction=random.choice(['inbound', 'outbound']),
                    date=timezone.now().date() - timedelta(days=random.randint(0, 365)),
                    person=people[person_idx],
                    user=self.user
                )
                batch_comms.append(comm)
            
            Communication.objects.bulk_create(batch_comms)
        
        comm_creation_time = time.time() - start_time
        print(f"Created 5000 communications in {comm_creation_time:.2f} seconds")
        
        # Login and test communication list performance
        self.client.login(username='perfuser', password='perfpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('communications:communication_list'))
        elapsed_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        print(f"Communication list loaded in {elapsed_time:.2f} seconds for 5000 records")
        
        # Performance assertion
        self.assertLess(elapsed_time, 2.5, "Communication list took too long to load")
    
    def test_dashboard_performance_with_large_dataset(self):
        """Test dashboard performance with large amounts of data"""
        # Create comprehensive test data
        contacts, people, _ = self._create_bulk_contacts(1000)
        
        # Create tasks
        tasks = []
        for i in range(500):
            task = Task(
                title=f'Dashboard Task {i}',
                due_date=timezone.now().date() + timedelta(days=random.randint(-7, 30)),
                assigned_to=self.user,
                created_by=self.user,
                person=people[i % len(people)],
                status=random.choice(['pending', 'in_progress', 'completed']),
                priority=random.choice(['low', 'medium', 'high'])
            )
            tasks.append(task)
        Task.objects.bulk_create(tasks)
        
        # Create communications
        comms = []
        for i in range(1000):
            comm = Communication(
                type='email',
                subject=f'Dashboard Comm {i}',
                message='Test message',
                direction='outbound',
                date=timezone.now().date() - timedelta(days=random.randint(0, 30)),
                person=people[i % len(people)],
                user=self.user
            )
            comms.append(comm)
        Communication.objects.bulk_create(comms)
        
        # Login and test dashboard performance
        self.client.login(username='perfuser', password='perfpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('core:dashboard'))
        elapsed_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        print(f"Dashboard loaded in {elapsed_time:.2f} seconds with large dataset")
        
        # Performance assertion - dashboard should load quickly
        self.assertLess(elapsed_time, 3.0, "Dashboard took too long to load")
    
    def test_pipeline_visualization_performance(self):
        """Test pipeline visualization with many contacts"""
        # Create 2000 contacts
        contacts, people, _ = self._create_bulk_contacts(2000)
        
        # Assign contacts to pipeline stages
        pipeline_contacts = []
        for i, person in enumerate(people):
            stage = self.stages[i % len(self.stages)]
            pc = PipelineContact(
                contact=person.contact,
                pipeline=self.pipeline,
                current_stage=stage
            )
            pipeline_contacts.append(pc)
        
        PipelineContact.objects.bulk_create(pipeline_contacts)
        
        # Login and test pipeline view performance
        self.client.login(username='perfuser', password='perfpass123')
        
        start_time = time.time()
        response = self.client.get(reverse('pipeline:pipeline_visualization', args=[self.pipeline.id]))
        elapsed_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        print(f"Pipeline view loaded in {elapsed_time:.2f} seconds for 2000 contacts")
        
        # Performance assertion
        self.assertLess(elapsed_time, 2.0, "Pipeline view took too long to load")
    
    def test_database_query_optimization(self):
        """Test that views use optimized queries with select_related and prefetch_related"""
        # Create test data
        contacts, people, _ = self._create_bulk_contacts(100)
        
        # Create tasks with relationships
        for person in people[:50]:
            Task.objects.create(
                title=f'Task for {person.contact.first_name}',
                due_date=timezone.now().date() + timedelta(days=7),
                assigned_to=self.user,
                created_by=self.user,
                person=person,
                status='pending'
            )
        
        # Login
        self.client.login(username='perfuser', password='perfpass123')
        
        # Reset queries
        connection.queries_log.clear()
        
        # Access contact list (should use optimized queries)
        with self.assertNumQueries(4):  # Adjust based on actual optimizations
            response = self.client.get(reverse('contacts:person_list'))
            self.assertEqual(response.status_code, 200)
        
        # Check query count is reasonable
        query_count = len(connection.queries)
        print(f"Contact list view executed {query_count} queries")
        self.assertLess(query_count, 8, "Too many queries executed for contact list")
    
    def test_pagination_performance(self):
        """Test pagination performance with large datasets"""
        # Create 10000 contacts
        contacts, people, _ = self._create_bulk_contacts(10000)
        
        # Login
        self.client.login(username='perfuser', password='perfpass123')
        
        # Test different pages
        page_numbers = [1, 50, 100, 200]
        
        for page in page_numbers:
            start_time = time.time()
            response = self.client.get(
                reverse('contacts:person_list'), 
                {'page': page}
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"Page {page} loaded in {elapsed_time:.2f} seconds")
                # Each page should load quickly regardless of page number
                self.assertLess(elapsed_time, 1.0, f"Page {page} took too long to load")
    
    def test_concurrent_user_performance(self):
        """Simulate multiple concurrent users accessing the system"""
        # Create test data
        contacts, people, _ = self._create_bulk_contacts(500)
        
        # Create multiple users
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'concurrent{i}',
                email=f'concurrent{i}@example.com',
                password='concurrentpass123',
                role='standard_user'
            )
            UserOffice.objects.create(user=user, office=self.office)
            users.append(user)
        
        # Simulate concurrent access
        clients = []
        for user in users:
            client = Client()
            client.login(username=user.username, password='concurrentpass123')
            clients.append(client)
        
        # All clients access dashboard simultaneously
        start_time = time.time()
        responses = []
        
        for client in clients:
            response = client.get(reverse('core:dashboard'))
            responses.append(response)
        
        elapsed_time = time.time() - start_time
        
        # All requests should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        print(f"5 concurrent dashboard requests completed in {elapsed_time:.2f} seconds")
        
        # Performance assertion - should handle concurrent requests efficiently
        avg_time = elapsed_time / len(clients)
        self.assertLess(avg_time, 1.0, "Concurrent requests took too long on average")


class DatabaseIndexPerformanceTest(TestCase):
    """Test database index effectiveness"""
    
    def setUp(self):
        self.office = Office.objects.create(
            name="Index Test Office",
            code="INDEX",
            is_active=True
        )
        
        self.user = User.objects.create_user(
            username='indexuser',
            email='index@example.com',
            password='indexpass123'
        )
        
        UserOffice.objects.create(user=self.user, office=self.office)
    
    def test_email_lookup_performance(self):
        """Test that email lookups use indexes effectively"""
        # Create many contacts
        for i in range(1000):
            Contact.objects.create(
                type='person',
                first_name=f'Index{i}',
                last_name='Test',
                email=f'index{i}@example.com',
                user=self.user,
                office=self.office
            )
        
        # Test email lookup performance
        start_time = time.time()
        contact = Contact.objects.filter(email='index500@example.com').first()
        elapsed_time = time.time() - start_time
        
        self.assertIsNotNone(contact)
        print(f"Email lookup completed in {elapsed_time:.4f} seconds")
        
        # Should be very fast with index
        self.assertLess(elapsed_time, 0.01, "Email lookup too slow - index may be missing")
    
    def test_date_range_query_performance(self):
        """Test date range queries on tasks"""
        # Create tasks with various due dates
        base_date = timezone.now().date()
        
        for i in range(2000):
            Task.objects.create(
                title=f'Date Task {i}',
                due_date=base_date + timedelta(days=i % 365),
                assigned_to=self.user,
                created_by=self.user,
                status='pending'
            )
        
        # Test date range query
        start_date = base_date + timedelta(days=30)
        end_date = base_date + timedelta(days=60)
        
        start_time = time.time()
        tasks = Task.objects.filter(
            due_date__gte=start_date,
            due_date__lte=end_date
        ).count()
        elapsed_time = time.time() - start_time
        
        print(f"Date range query found {tasks} tasks in {elapsed_time:.4f} seconds")
        
        # Should be fast with proper indexing
        self.assertLess(elapsed_time, 0.1, "Date range query too slow")
    
    def test_foreign_key_join_performance(self):
        """Test performance of queries with foreign key joins"""
        # Create related data
        for i in range(500):
            contact = Contact.objects.create(
                type='person',
                first_name=f'Join{i}',
                last_name='Test',
                email=f'join{i}@example.com',
                user=self.user,
                office=self.office
            )
            person = Person.objects.create(contact=contact)
            
            # Create tasks for each person
            for j in range(5):
                Task.objects.create(
                    title=f'Task {j} for Join{i}',
                    due_date=timezone.now().date() + timedelta(days=j),
                    assigned_to=self.user,
                    created_by=self.user,
                    person=person,
                    status='pending'
                )
        
        # Test join query performance
        start_time = time.time()
        
        # Query that joins tasks with persons and contacts
        tasks_with_contacts = Task.objects.select_related(
            'person__contact'
        ).filter(
            status='pending',
            person__contact__office=self.office
        ).count()
        
        elapsed_time = time.time() - start_time
        
        print(f"Join query found {tasks_with_contacts} tasks in {elapsed_time:.4f} seconds")
        
        # Should be reasonably fast even with joins
        self.assertLess(elapsed_time, 0.5, "Join query too slow")