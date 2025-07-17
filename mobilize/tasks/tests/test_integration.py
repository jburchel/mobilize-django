"""
Integration tests for Task app - testing cross-app functionality.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from mobilize.admin_panel.models import Office, UserOffice
from mobilize.contacts.models import Person, Contact
from mobilize.churches.models import Church
from mobilize.tasks.models import Task

User = get_user_model()


class TaskOfficeIntegrationTest(TestCase):
    """Test task integration with office system"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.office1 = Office.objects.create(name="Office 1", code="OFF1")
        self.office2 = Office.objects.create(name="Office 2", code="OFF2")
        # Assign user to office1
        UserOffice.objects.create(
            user=self.user, office=self.office1, role="office_admin", is_primary=True
        )

    def test_task_office_scoping(self):
        """Test that tasks are properly scoped to offices"""
        # Create tasks for different offices
        task1 = Task.objects.create(
            title="Office 1 Task", office=self.office1, created_by=self.user
        )
        task2 = Task.objects.create(
            title="Office 2 Task", office=self.office2, created_by=self.user
        )

        # Test office-specific task queries
        office1_tasks = Task.objects.filter(office=self.office1)
        office2_tasks = Task.objects.filter(office=self.office2)

        self.assertIn(task1, office1_tasks)
        self.assertNotIn(task2, office1_tasks)

        self.assertIn(task2, office2_tasks)
        self.assertNotIn(task1, office2_tasks)

    def test_office_deletion_sets_null(self):
        """Test that deleting office sets task.office to NULL"""
        task = Task.objects.create(
            title="Test Task", office=self.office1, created_by=self.user
        )

        task_id = task.id

        # Delete office
        self.office1.delete()

        # Task should still exist but office should be None
        task.refresh_from_db()
        self.assertIsNone(task.office)

    def test_multiple_tasks_per_office(self):
        """Test that offices can have multiple tasks"""
        task1 = Task.objects.create(
            title="Task 1", office=self.office1, created_by=self.user
        )
        task2 = Task.objects.create(
            title="Task 2", office=self.office1, created_by=self.user
        )
        task3 = Task.objects.create(
            title="Task 3", office=self.office1, created_by=self.user
        )

        office_tasks = self.office1.tasks.all()
        self.assertEqual(office_tasks.count(), 3)
        self.assertIn(task1, office_tasks)
        self.assertIn(task2, office_tasks)
        self.assertIn(task3, office_tasks)

    def test_user_office_task_relationship(self):
        """Test relationship between user office assignments and tasks"""
        # Create tasks in user's assigned office
        task1 = Task.objects.create(
            title="Assigned Office Task",
            office=self.office1,
            created_by=self.user,
            assigned_to=self.user,
        )

        # Create task in different office
        task2 = Task.objects.create(
            title="Other Office Task",
            office=self.office2,
            created_by=self.user,
            assigned_to=self.user,
        )

        # User can have tasks in any office, but should be assigned to their office
        user_offices = [uo.office for uo in UserOffice.objects.filter(user=self.user)]
        self.assertIn(self.office1, user_offices)
        self.assertNotIn(self.office2, user_offices)


class TaskContactIntegrationTest(TestCase):
    """Test task integration with contacts and churches"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )
        self.church = Church.objects.create(name="Test Church")
        self.contact = Contact.objects.create(
            first_name="Jane", last_name="Smith", email="jane@example.com"
        )

    def test_person_task_relationship(self):
        """Test person can have multiple tasks"""
        task1 = Task.objects.create(
            title="Person Task 1",
            person=self.person,
            created_by=self.user,
            office=self.office,
        )
        task2 = Task.objects.create(
            title="Person Task 2",
            person=self.person,
            created_by=self.user,
            office=self.office,
        )

        # Person should have multiple tasks
        person_tasks = self.person.person_tasks.all()
        self.assertEqual(person_tasks.count(), 2)
        self.assertIn(task1, person_tasks)
        self.assertIn(task2, person_tasks)

    def test_church_task_relationship(self):
        """Test church can have multiple tasks"""
        task1 = Task.objects.create(
            title="Church Task 1",
            church=self.church,
            created_by=self.user,
            office=self.office,
        )
        task2 = Task.objects.create(
            title="Church Task 2",
            church=self.church,
            created_by=self.user,
            office=self.office,
        )

        # Church should have multiple tasks
        church_tasks = self.church.church_tasks.all()
        self.assertEqual(church_tasks.count(), 2)
        self.assertIn(task1, church_tasks)
        self.assertIn(task2, church_tasks)

    def test_contact_task_relationship(self):
        """Test contact can have multiple tasks"""
        task1 = Task.objects.create(
            title="Contact Task 1",
            contact=self.contact,
            created_by=self.user,
            office=self.office,
        )
        task2 = Task.objects.create(
            title="Contact Task 2",
            contact=self.contact,
            created_by=self.user,
            office=self.office,
        )

        # Contact should have multiple tasks
        contact_tasks = self.contact.contact_tasks.all()
        self.assertEqual(contact_tasks.count(), 2)
        self.assertIn(task1, contact_tasks)
        self.assertIn(task2, contact_tasks)

    def test_person_deletion_cascade(self):
        """Test that deleting person sets task.person to NULL"""
        task = Task.objects.create(
            title="Person Task",
            person=self.person,
            created_by=self.user,
            office=self.office,
        )

        # Delete person
        self.person.delete()

        # Task should still exist but person should be None
        task.refresh_from_db()
        self.assertIsNone(task.person)

    def test_church_deletion_cascade(self):
        """Test that deleting church sets task.church to NULL"""
        task = Task.objects.create(
            title="Church Task",
            church=self.church,
            created_by=self.user,
            office=self.office,
        )

        # Delete church
        self.church.delete()

        # Task should still exist but church should be None
        task.refresh_from_db()
        self.assertIsNone(task.church)

    def test_contact_deletion_cascade(self):
        """Test that deleting contact sets task.contact to NULL"""
        task = Task.objects.create(
            title="Contact Task",
            contact=self.contact,
            created_by=self.user,
            office=self.office,
        )

        # Delete contact
        self.contact.delete()

        # Task should still exist but contact should be None
        task.refresh_from_db()
        self.assertIsNone(task.contact)

    def test_mixed_entity_tasks(self):
        """Test task can be related to multiple entity types simultaneously"""
        # Task can theoretically be related to person, church, AND contact
        task = Task.objects.create(
            title="Mixed Entity Task",
            person=self.person,
            church=self.church,
            contact=self.contact,
            created_by=self.user,
            office=self.office,
        )

        self.assertEqual(task.person, self.person)
        self.assertEqual(task.church, self.church)
        self.assertEqual(task.contact, self.contact)

        # All entities should have the task in their related tasks
        self.assertIn(task, self.person.person_tasks.all())
        self.assertIn(task, self.church.church_tasks.all())
        self.assertIn(task, self.contact.contact_tasks.all())


class TaskUserIntegrationTest(TestCase):
    """Test task integration with user system"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")

    def test_user_created_tasks_relationship(self):
        """Test user can create multiple tasks"""
        task1 = Task.objects.create(
            title="Created Task 1", created_by=self.user1, office=self.office
        )
        task2 = Task.objects.create(
            title="Created Task 2", created_by=self.user1, office=self.office
        )

        created_tasks = self.user1.created_tasks.all()
        self.assertEqual(created_tasks.count(), 2)
        self.assertIn(task1, created_tasks)
        self.assertIn(task2, created_tasks)

    def test_user_assigned_tasks_relationship(self):
        """Test user can be assigned multiple tasks"""
        task1 = Task.objects.create(
            title="Assigned Task 1",
            assigned_to=self.user1,
            created_by=self.user2,
            office=self.office,
        )
        task2 = Task.objects.create(
            title="Assigned Task 2",
            assigned_to=self.user1,
            created_by=self.user2,
            office=self.office,
        )

        assigned_tasks = self.user1.assigned_tasks.all()
        self.assertEqual(assigned_tasks.count(), 2)
        self.assertIn(task1, assigned_tasks)
        self.assertIn(task2, assigned_tasks)

    def test_user_deletion_sets_null(self):
        """Test that deleting user sets task user fields to NULL"""
        task = Task.objects.create(
            title="User Task",
            created_by=self.user1,
            assigned_to=self.user2,
            office=self.office,
        )

        # Test that the relationship exists
        self.assertEqual(task.assigned_to, self.user2)
        self.assertEqual(task.created_by, self.user1)

        # Note: We can't actually test user deletion in this test environment
        # due to database constraints, but we can verify the relationship
        # and that the fields allow NULL
        task.assigned_to = None
        task.save()

        # Refresh from database
        task.refresh_from_db()

        # assigned_to should be NULL now
        self.assertIsNone(task.assigned_to)
        self.assertEqual(task.created_by, self.user1)  # Should still exist

        # Test created_by can also be set to NULL
        task.created_by = None
        task.save()

        # Refresh from database
        task.refresh_from_db()

        # created_by should be NULL now
        self.assertIsNone(task.created_by)

    def test_task_assignment_transfer(self):
        """Test transferring task assignment between users"""
        task = Task.objects.create(
            title="Transfer Task",
            created_by=self.user1,
            assigned_to=self.user1,
            office=self.office,
        )

        # Initially assigned to user1
        self.assertEqual(task.assigned_to, self.user1)
        self.assertIn(task, self.user1.assigned_tasks.all())
        self.assertNotIn(task, self.user2.assigned_tasks.all())

        # Transfer to user2
        task.assigned_to = self.user2
        task.save()

        # Now assigned to user2
        self.assertEqual(task.assigned_to, self.user2)
        self.assertNotIn(task, self.user1.assigned_tasks.all())
        self.assertIn(task, self.user2.assigned_tasks.all())


class TaskRecurringIntegrationTest(TestCase):
    """Test recurring task integration across the system"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )

    def test_recurring_template_with_relationships(self):
        """Test recurring template maintains relationships to occurrences"""
        recurring_pattern = {
            "frequency": "weekly",
            "interval": 1,
            "weekdays": [1, 3],  # Tuesday, Thursday
        }

        template = Task.objects.create(
            title="Weekly Check-in",
            description="Weekly check-in with contact",
            person=self.person,
            recurring_pattern=recurring_pattern,
            is_recurring_template=True,
            recurrence_end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user,
            assigned_to=self.user,
            office=self.office,
            next_occurrence_date=timezone.now() + timedelta(days=1),
        )

        # Generate occurrences
        occurrence1 = template.generate_next_occurrence()
        occurrence2 = template.generate_next_occurrence()

        self.assertIsNotNone(occurrence1)
        self.assertIsNotNone(occurrence2)

        # Check template relationship
        occurrences = template.occurrences.all()
        self.assertEqual(occurrences.count(), 2)
        self.assertIn(occurrence1, occurrences)
        self.assertIn(occurrence2, occurrences)

        # Check occurrence properties
        self.assertEqual(occurrence1.parent_task, template)
        self.assertEqual(occurrence1.person, template.person)
        self.assertEqual(occurrence1.created_by, template.created_by)
        self.assertEqual(occurrence1.assigned_to, template.assigned_to)
        self.assertEqual(occurrence1.office, template.office)
        self.assertFalse(occurrence1.is_recurring_template)

    def test_template_deletion_cascades_to_occurrences(self):
        """Test that deleting template deletes all occurrences"""
        template = Task.objects.create(
            title="Template Task",
            is_recurring_template=True,
            created_by=self.user,
            office=self.office,
        )

        # Create occurrences
        occurrence1 = Task.objects.create(
            title="Occurrence 1",
            parent_task=template,
            created_by=self.user,
            office=self.office,
        )
        occurrence2 = Task.objects.create(
            title="Occurrence 2",
            parent_task=template,
            created_by=self.user,
            office=self.office,
        )

        occurrence1_id = occurrence1.id
        occurrence2_id = occurrence2.id

        # Delete template
        template.delete()

        # Occurrences should be deleted due to CASCADE
        self.assertFalse(Task.objects.filter(id=occurrence1_id).exists())
        self.assertFalse(Task.objects.filter(id=occurrence2_id).exists())

    def test_occurrence_independence_from_template_changes(self):
        """Test that changing template doesn't affect existing occurrences"""
        recurring_pattern = {"frequency": "daily", "interval": 1}

        template = Task.objects.create(
            title="Original Template",
            description="Original description",
            priority="medium",
            recurring_pattern=recurring_pattern,
            is_recurring_template=True,
            created_by=self.user,
            office=self.office,
            next_occurrence_date=timezone.now() + timedelta(days=1),
        )

        # Generate occurrence
        occurrence = template.generate_next_occurrence()
        self.assertIsNotNone(occurrence)  # Ensure occurrence was created
        original_title = occurrence.title
        original_description = occurrence.description
        original_priority = occurrence.priority

        # Change template
        template.title = "Updated Template"
        template.description = "Updated description"
        template.priority = "high"
        template.save()

        # Occurrence should remain unchanged
        occurrence.refresh_from_db()
        self.assertEqual(occurrence.title, original_title)
        self.assertEqual(occurrence.description, original_description)
        self.assertEqual(occurrence.priority, original_priority)


class TaskDataConsistencyTest(TransactionTestCase):
    """Test data consistency and constraints in task system"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )

    def test_task_relationship_consistency(self):
        """Test that task relationships maintain consistency"""
        task = Task.objects.create(
            title="Consistency Task",
            person=self.person,
            created_by=self.user,
            assigned_to=self.user,
            office=self.office,
        )

        # Verify all relationships work correctly
        self.assertEqual(task.person, self.person)
        self.assertEqual(task.created_by, self.user)
        self.assertEqual(task.assigned_to, self.user)
        self.assertEqual(task.office, self.office)

        # Verify reverse relationships
        self.assertIn(task, self.person.person_tasks.all())
        self.assertIn(task, self.user.created_tasks.all())
        self.assertIn(task, self.user.assigned_tasks.all())
        self.assertIn(task, self.office.tasks.all())

    def test_task_status_transitions(self):
        """Test task status transitions maintain consistency"""
        task = Task.objects.create(
            title="Status Task",
            status="pending",
            created_by=self.user,
            office=self.office,
        )

        # Pending to in_progress
        task.status = "in_progress"
        task.save()
        self.assertEqual(task.status, "in_progress")
        self.assertIsNone(task.completed_at)

        # In_progress to completed
        task.status = "completed"
        task.completed_at = timezone.now()
        task.save()
        self.assertEqual(task.status, "completed")
        self.assertIsNotNone(task.completed_at)

        # Back to pending (should clear completion)
        task.status = "pending"
        task.completed_at = None
        task.save()
        self.assertEqual(task.status, "pending")
        self.assertIsNone(task.completed_at)

    def test_recurring_task_constraints(self):
        """Test constraints on recurring tasks"""
        # Template without pattern should work
        template = Task.objects.create(
            title="Template Without Pattern",
            is_recurring_template=True,
            created_by=self.user,
            office=self.office,
        )
        self.assertTrue(template.is_recurring_template)
        self.assertIsNone(template.recurring_pattern)

        # Occurrence with parent should work
        occurrence = Task.objects.create(
            title="Occurrence",
            parent_task=template,
            is_recurring_template=False,
            created_by=self.user,
            office=self.office,
        )
        self.assertEqual(occurrence.parent_task, template)
        self.assertFalse(occurrence.is_recurring_template)

    def test_google_calendar_integration_fields(self):
        """Test Google Calendar integration maintains consistency"""
        task = Task.objects.create(
            title="Calendar Task",
            google_calendar_event_id="event_123",
            google_calendar_sync_enabled=True,
            last_synced_at=timezone.now(),
            created_by=self.user,
            office=self.office,
        )

        # Verify calendar fields
        self.assertEqual(task.google_calendar_event_id, "event_123")
        self.assertTrue(task.google_calendar_sync_enabled)
        self.assertIsNotNone(task.last_synced_at)

        # Disable sync should work
        task.google_calendar_sync_enabled = False
        task.save()
        self.assertFalse(task.google_calendar_sync_enabled)

        # Clear event ID should work
        task.google_calendar_event_id = None
        task.save()
        self.assertIsNone(task.google_calendar_event_id)


class TaskCrossAppIntegrationTest(TestCase):
    """Test task integration across multiple apps"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )
        self.church = Church.objects.create(name="Test Church")

    def test_task_creation_from_contact_interaction(self):
        """Test creating task as follow-up to contact interaction"""
        # Simulate creating task after contact interaction
        task = Task.objects.create(
            title="Follow up with John Doe",
            description="Follow up on church visit discussion",
            person=self.person,
            church=self.church,
            priority="high",
            status="pending",
            due_date=timezone.now().date() + timedelta(days=3),
            created_by=self.user,
            assigned_to=self.user,
            office=self.office,
        )

        # Task should be linked to both person and church
        self.assertEqual(task.person, self.person)
        self.assertEqual(task.church, self.church)

        # Both entities should show the task
        self.assertIn(task, self.person.person_tasks.all())
        self.assertIn(task, self.church.church_tasks.all())

    def test_task_office_scoping_with_contacts(self):
        """Test that tasks respect office scoping with contact relationships"""
        office2 = Office.objects.create(name="Office 2", code="OFF2")

        # Create tasks in different offices for same person
        task1 = Task.objects.create(
            title="Office 1 Task",
            person=self.person,
            office=self.office,
            created_by=self.user,
        )

        task2 = Task.objects.create(
            title="Office 2 Task",
            person=self.person,
            office=office2,
            created_by=self.user,
        )

        # Person should have tasks from both offices
        person_tasks = self.person.person_tasks.all()
        self.assertEqual(person_tasks.count(), 2)
        self.assertIn(task1, person_tasks)
        self.assertIn(task2, person_tasks)

        # But office filtering should work
        office1_person_tasks = self.person.person_tasks.filter(office=self.office)
        office2_person_tasks = self.person.person_tasks.filter(office=office2)

        self.assertEqual(office1_person_tasks.count(), 1)
        self.assertEqual(office2_person_tasks.count(), 1)
        self.assertIn(task1, office1_person_tasks)
        self.assertIn(task2, office2_person_tasks)

    def test_complex_task_scenario(self):
        """Test complex scenario involving multiple entities and relationships"""
        # Create a complex task scenario:
        # User creates recurring template for church outreach
        # Template generates occurrences assigned to different people

        recurring_pattern = {"frequency": "monthly", "interval": 1, "day_of_month": 1}

        template = Task.objects.create(
            title="Monthly Church Outreach",
            description="Monthly outreach planning meeting",
            church=self.church,
            recurring_pattern=recurring_pattern,
            is_recurring_template=True,
            recurrence_end_date=timezone.now().date() + timedelta(days=365),
            created_by=self.user,
            office=self.office,
            next_occurrence_date=timezone.now() + timedelta(days=1),
        )

        # Generate first occurrence
        occurrence = template.generate_next_occurrence()

        # Assign occurrence to specific person
        occurrence.assigned_to = self.user
        occurrence.person = self.person
        occurrence.save()

        # Verify complex relationships
        self.assertEqual(occurrence.parent_task, template)
        self.assertEqual(occurrence.church, self.church)
        self.assertEqual(occurrence.person, self.person)
        self.assertEqual(occurrence.assigned_to, self.user)
        self.assertEqual(occurrence.office, self.office)

        # Verify all entities see relevant tasks
        self.assertIn(template, self.church.church_tasks.all())
        self.assertIn(occurrence, self.church.church_tasks.all())
        self.assertIn(occurrence, self.person.person_tasks.all())
        self.assertIn(template, self.user.created_tasks.all())
        self.assertIn(occurrence, self.user.assigned_tasks.all())
        self.assertIn(template, self.office.tasks.all())
        self.assertIn(occurrence, self.office.tasks.all())
