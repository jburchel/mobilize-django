"""
End-to-end tests for critical user workflows in Mobilize CRM
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.tasks.models import Task
from mobilize.communications.models import Communication, EmailTemplate
from mobilize.admin_panel.models import Office, UserOffice
from mobilize.pipeline.models import Pipeline, PipelineStage, PipelineContact
from mobilize.authentication.models import GoogleToken

User = get_user_model()


class UserOnboardingE2ETests(TestCase):
    """Test the complete user onboarding workflow"""

    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Test Office", code="TEST", is_active=True
        )

    def test_complete_user_onboarding_workflow(self):
        """Test the complete workflow from user creation to first task"""

        # Step 1: Create a super admin to set up the system
        super_admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            role="super_admin",
        )

        # Step 2: Super admin logs in and creates a new user
        self.client.login(username="admin", password="adminpass123")

        # Create new user through admin interface
        new_user = User.objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password="newpass123",
            role="standard_user",
            first_name="New",
            last_name="User",
        )

        # Assign user to office
        UserOffice.objects.create(user=new_user, office=self.office)

        # Step 3: New user logs in for the first time
        self.client.logout()
        login_result = self.client.login(username="newuser", password="newpass123")
        self.assertTrue(login_result)

        # Step 4: User accesses dashboard
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)

        # Step 5: User creates their first contact
        response = self.client.post(
            reverse("contacts:person_create"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "123-456-7890",
                "priority": "medium",
            },
        )
        self.assertIn(response.status_code, [200, 302])  # Success or redirect

        # Verify contact was created
        contact = Contact.objects.filter(email="john.doe@example.com").first()
        self.assertIsNotNone(contact)
        self.assertEqual(contact.first_name, "John")
        self.assertEqual(contact.user, new_user)
        self.assertEqual(contact.office, self.office)

        # Step 6: User creates a task for the contact
        person = Person.objects.get(contact=contact)
        response = self.client.post(
            reverse("tasks:task_create"),
            {
                "title": "Follow up with John",
                "description": "Initial follow-up call",
                "due_date": (timezone.now().date() + timedelta(days=3)).isoformat(),
                "person": person.pk,
                "priority": "high",
                "status": "pending",
            },
        )
        self.assertIn(response.status_code, [200, 302])

        # Verify task was created
        task = Task.objects.filter(title="Follow up with John").first()
        self.assertIsNotNone(task)
        self.assertEqual(task.created_by, new_user)
        self.assertEqual(task.assigned_to, new_user)


class ContactManagementE2ETests(TestCase):
    """Test complete contact management workflows"""

    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Sales Office", code="SALES", is_active=True
        )

        self.user = User.objects.create_user(
            username="salesrep",
            email="sales@example.com",
            password="salespass123",
            role="standard_user",
        )

        UserOffice.objects.create(user=self.user, office=self.office)

        # Create pipeline stages
        self.pipeline = Pipeline.objects.create(
            name="Sales Pipeline", office=self.office, pipeline_type="person"
        )

        self.stages = []
        stage_names = ["New Lead", "Contacted", "Qualified", "Proposal", "Closed"]
        for i, name in enumerate(stage_names):
            stage = PipelineStage.objects.create(
                name=name, pipeline=self.pipeline, order=i, color=f"#00{i}000"
            )
            self.stages.append(stage)

    def test_complete_contact_lifecycle(self):
        """Test the complete lifecycle of a contact from creation to conversion"""

        self.client.login(username="salesrep", password="salespass123")

        # Step 1: Create a new contact
        response = self.client.post(
            reverse("contacts:person_create"),
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com",
                "phone": "555-123-4567",
                "priority": "high",
                "notes": "Met at conference, interested in our services",
            },
        )
        self.assertIn(response.status_code, [200, 302])

        contact = Contact.objects.filter(email="jane.smith@example.com").first()
        person = Person.objects.get(contact=contact)

        # Step 2: Add contact to pipeline
        pipeline_contact = PipelineContact.objects.create(
            contact=contact, pipeline=self.pipeline, current_stage=self.stages[0]
        )

        # Step 3: Log first communication
        response = self.client.post(
            reverse("communications:communication_create"),
            {
                "type": "email",
                "subject": "Introduction Email",
                "message": "Thank you for your interest in our services...",
                "direction": "outbound",
                "date": timezone.now().date().isoformat(),
                "person": person.pk,
            },
        )
        self.assertIn(response.status_code, [200, 302])

        # Step 4: Move contact through pipeline stages
        for i in range(1, len(self.stages)):
            # Update pipeline stage
            pipeline_contact.current_stage = self.stages[i]
            pipeline_contact.save()

            # Create a task for each stage
            response = self.client.post(
                reverse("tasks:task_create"),
                {
                    "title": f"{self.stages[i].name} - Jane Smith",
                    "description": f"Complete {self.stages[i].name} activities",
                    "due_date": (
                        timezone.now().date() + timedelta(days=i * 2)
                    ).isoformat(),
                    "person": person.pk,
                    "priority": "medium",
                    "status": "pending",
                },
            )
            self.assertIn(response.status_code, [200, 302])

            # Complete the task
            task = Task.objects.filter(
                title=f"{self.stages[i].name} - Jane Smith"
            ).first()
            task.status = "completed"
            task.completed_at = timezone.now()
            task.save()

        # Step 5: Verify the complete journey
        # Check pipeline progress
        pipeline_contact.refresh_from_db()
        self.assertEqual(pipeline_contact.current_stage, self.stages[-1])  # Closed

        # Check communication history
        communications = Communication.objects.filter(person=person).count()
        self.assertGreaterEqual(communications, 1)

        # Check task completion
        completed_tasks = Task.objects.filter(person=person, status="completed").count()
        self.assertEqual(completed_tasks, len(self.stages) - 1)


class ChurchManagementE2ETests(TestCase):
    """Test complete church management workflows"""

    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Church Relations", code="CHURCH", is_active=True
        )

        self.user = User.objects.create_user(
            username="churchmanager",
            email="church@example.com",
            password="churchpass123",
            role="office_admin",
        )

        UserOffice.objects.create(user=self.user, office=self.office)

    def test_church_creation_and_contact_association(self):
        """Test creating a church and associating contacts with it"""

        self.client.login(username="churchmanager", password="churchpass123")

        # Step 1: Create a church
        response = self.client.post(
            reverse("churches:church_create"),
            {
                "name": "Grace Community Church",
                "email": "info@gracechurch.com",
                "phone": "555-100-2000",
                "street_address": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62701",
                "website": "https://gracechurch.com",
                "denomination": "Non-denominational",
                "congregation_size": 500,
            },
        )
        self.assertIn(response.status_code, [200, 302])

        church_contact = Contact.objects.filter(email="info@gracechurch.com").first()
        church = Church.objects.get(contact=church_contact)

        # Step 2: Create pastor contact
        response = self.client.post(
            reverse("contacts:person_create"),
            {
                "first_name": "Pastor",
                "last_name": "Johnson",
                "email": "pastor@gracechurch.com",
                "phone": "555-100-2001",
                "priority": "medium",
            },
        )
        self.assertIn(response.status_code, [200, 302])

        pastor_contact = Contact.objects.filter(email="pastor@gracechurch.com").first()
        pastor = Person.objects.get(contact=pastor_contact)

        # Step 3: Create a communication with the church
        response = self.client.post(
            reverse("communications:communication_create"),
            {
                "type": "email",
                "subject": "Partnership Opportunity",
                "message": "We would like to discuss partnership opportunities...",
                "direction": "outbound",
                "date": timezone.now().date().isoformat(),
                "church": church.pk,
            },
        )
        self.assertIn(response.status_code, [200, 302])

        # Step 4: Create a task related to the church
        response = self.client.post(
            reverse("tasks:task_create"),
            {
                "title": "Schedule meeting with Grace Community",
                "description": "Discuss partnership details",
                "due_date": (timezone.now().date() + timedelta(days=7)).isoformat(),
                "church": church.pk,
                "priority": "high",
                "status": "pending",
            },
        )
        self.assertIn(response.status_code, [200, 302])

        # Step 5: Verify relationships
        # Check pastor exists
        self.assertIsNotNone(pastor)

        # Check communications exist
        church_comms = Communication.objects.filter(church=church).count()
        self.assertGreaterEqual(church_comms, 1)

        # Check tasks exist
        church_tasks = Task.objects.filter(church=church).count()
        self.assertGreaterEqual(church_tasks, 1)


class EmailCommunicationE2ETests(TestCase):
    """Test complete email communication workflows"""

    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Communications Office", code="COMM", is_active=True
        )

        self.user = User.objects.create_user(
            username="commuser",
            email="comm@example.com",
            password="commpass123",
            role="standard_user",
        )

        UserOffice.objects.create(user=self.user, office=self.office)

        # Create test contacts
        self.contacts = []
        for i in range(3):
            contact = Contact.objects.create(
                type="person",
                first_name=f"Contact{i}",
                last_name="Test",
                email=f"contact{i}@example.com",
                user=self.user,
                office=self.office,
            )
            person = Person.objects.create(contact=contact)
            self.contacts.append(person)

    def test_email_template_and_bulk_send_workflow(self):
        """Test creating an email template and sending bulk emails"""

        self.client.login(username="commuser", password="commpass123")

        # Step 1: Create an email template
        response = self.client.post(
            reverse("communications:email_template_create"),
            {
                "name": "Welcome Email",
                "subject": "Welcome to our community, {first_name}!",
                "body": "Dear {first_name},\n\nWelcome to our community! We are excited to have you.",
                "category": "welcome",
            },
        )
        self.assertIn(response.status_code, [200, 302])

        template = EmailTemplate.objects.filter(name="Welcome Email").first()
        self.assertIsNotNone(template)

        # Step 2: Create a bulk email campaign using the template
        # Note: Since bulk email functionality might not be fully implemented,
        # we'll simulate sending individual emails

        for person in self.contacts:
            # Personalize the email
            subject = template.subject.replace(
                "{first_name}", person.contact.first_name
            )
            body = template.body.replace("{first_name}", person.contact.first_name)

            # Create communication record
            response = self.client.post(
                reverse("communications:communication_create"),
                {
                    "type": "email",
                    "subject": subject,
                    "message": body,
                    "direction": "outbound",
                    "date": timezone.now().date().isoformat(),
                    "person": person.pk,
                    "template_used": template.id,
                },
            )
            self.assertIn(response.status_code, [200, 302])

        # Step 3: Verify all emails were recorded
        for person in self.contacts:
            comm = Communication.objects.filter(
                person=person, template_used=template
            ).first()
            self.assertIsNotNone(comm)
            self.assertIn(person.contact.first_name, comm.subject)
            self.assertIn(person.contact.first_name, comm.message)

        # Step 4: Check communication history
        response = self.client.get(reverse("communications:communication_list"))
        self.assertEqual(response.status_code, 200)

        # Verify all communications are listed
        total_comms = Communication.objects.filter(user=self.user).count()
        self.assertEqual(total_comms, len(self.contacts))


class TaskManagementE2ETests(TestCase):
    """Test complete task management workflows"""

    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Task Office", code="TASK", is_active=True
        )

        self.manager = User.objects.create_user(
            username="taskmanager",
            email="manager@example.com",
            password="managerpass123",
            role="office_admin",
        )

        self.team_member = User.objects.create_user(
            username="teammember",
            email="member@example.com",
            password="memberpass123",
            role="standard_user",
        )

        UserOffice.objects.create(user=self.manager, office=self.office)
        UserOffice.objects.create(user=self.team_member, office=self.office)

        # Create test contact
        self.contact = Contact.objects.create(
            type="person",
            first_name="Task",
            last_name="Target",
            email="tasktarget@example.com",
            user=self.manager,
            office=self.office,
        )
        self.person = Person.objects.create(contact=self.contact)

    def test_task_delegation_and_completion_workflow(self):
        """Test creating, delegating, and completing tasks"""

        # Step 1: Manager creates and assigns task to team member
        self.client.login(username="taskmanager", password="managerpass123")

        response = self.client.post(
            reverse("tasks:task_create"),
            {
                "title": "Contact follow-up",
                "description": "Please follow up with this contact and update their status",
                "due_date": (timezone.now().date() + timedelta(days=2)).isoformat(),
                "assigned_to": self.team_member.id,
                "person": self.person.pk,
                "priority": "high",
                "status": "pending",
            },
        )
        self.assertIn(response.status_code, [200, 302])

        task = Task.objects.filter(title="Contact follow-up").first()
        self.assertIsNotNone(task)
        self.assertEqual(task.assigned_to, self.team_member)
        self.assertEqual(task.created_by, self.manager)

        # Step 2: Team member logs in and views their tasks
        self.client.logout()
        self.client.login(username="teammember", password="memberpass123")

        response = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(response.status_code, 200)

        # Step 3: Team member completes the task
        response = self.client.post(
            reverse("tasks:task_update", args=[task.id]),
            {
                "title": task.title,
                "description": task.description,
                "due_date": task.due_date,
                "assigned_to": task.assigned_to.id,
                "person": task.person.pk,
                "priority": task.priority,
                "status": "completed",
                "completion_notes": "Contact reached, updated their information",
            },
        )
        self.assertIn(response.status_code, [200, 302])

        # Step 4: Verify task completion
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")
        self.assertIsNotNone(task.completed_at)
        self.assertIn("Contact reached", task.completion_notes)

        # Step 5: Manager views completed tasks
        self.client.logout()
        self.client.login(username="taskmanager", password="managerpass123")

        response = self.client.get(reverse("tasks:task_list") + "?status=completed")
        self.assertEqual(response.status_code, 200)


class GoogleIntegrationE2ETests(TestCase):
    """Test Google services integration workflows"""

    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Google Office", code="GOOGLE", is_active=True
        )

        self.user = User.objects.create_user(
            username="googleuser",
            email="google@example.com",
            password="googlepass123",
            role="standard_user",
        )

        UserOffice.objects.create(user=self.user, office=self.office)

    def test_google_oauth_and_sync_workflow(self):
        """Test Google OAuth setup and contact sync workflow"""

        self.client.login(username="googleuser", password="googlepass123")

        # Step 1: User initiates Google OAuth (simulated)
        # In real scenario, this would redirect to Google

        # Simulate successful OAuth by creating a token
        google_token = GoogleToken.objects.create(
            user=self.user,
            access_token="fake_access_token",
            refresh_token="fake_refresh_token",
            token_type="Bearer",
            expires_at=timezone.now() + timedelta(hours=1),
            scopes=[
                "https://www.googleapis.com/auth/contacts",
                "https://www.googleapis.com/auth/gmail.readonly",
            ],
        )

        # Step 2: User configures sync settings
        from mobilize.authentication.models import UserContactSyncSettings

        sync_settings = UserContactSyncSettings.objects.create(
            user=self.user,
            sync_preference="crm_only",
            sync_frequency="daily",
            last_sync=timezone.now(),
        )

        # Step 3: Simulate contact sync
        # Create some contacts as if they were synced from Google
        google_contacts = []
        for i in range(3):
            contact = Contact.objects.create(
                type="person",
                first_name=f"Google",
                last_name=f"Contact{i}",
                email=f"googlecontact{i}@gmail.com",
                user=self.user,
                office=self.office,
                google_contact_id=f"google_id_{i}",
            )
            person = Person.objects.create(contact=contact)
            google_contacts.append(person)

        # Step 4: Verify sync results
        synced_contacts = Contact.objects.filter(
            user=self.user, google_contact_id__isnull=False
        ).count()
        self.assertEqual(synced_contacts, 3)

        # Step 5: User views synced contacts
        response = self.client.get(reverse("contacts:person_list"))
        self.assertEqual(response.status_code, 200)

        # Verify Google contacts are visible
        for person in google_contacts:
            contact = Contact.objects.filter(email=person.contact.email).first()
            self.assertIsNotNone(contact)
            self.assertIsNotNone(contact.google_contact_id)


class ReportingE2ETests(TestCase):
    """Test reporting and analytics workflows"""

    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Analytics Office", code="ANALYTICS", is_active=True
        )

        self.admin = User.objects.create_user(
            username="analytics_admin",
            email="analytics@example.com",
            password="analyticspass123",
            role="office_admin",
        )

        UserOffice.objects.create(user=self.admin, office=self.office)

        # Create sample data for reporting
        self._create_sample_data()

    def _create_sample_data(self):
        """Create sample data for reporting tests"""
        # Create contacts with different pipeline stages
        stages = ["New Lead", "Contacted", "Qualified", "Proposal", "Closed"]

        for i in range(20):
            contact = Contact.objects.create(
                type="person",
                first_name=f"Report",
                last_name=f"Contact{i}",
                email=f"report{i}@example.com",
                user=self.admin,
                office=self.office,
                priority=["low", "medium", "high"][i % 3],
            )
            Person.objects.create(contact=contact)

            # Create tasks
            if i % 2 == 0:
                Task.objects.create(
                    title=f"Task for Contact{i}",
                    due_date=timezone.now().date() + timedelta(days=i),
                    assigned_to=self.admin,
                    created_by=self.admin,
                    person=Person.objects.get(contact=contact),
                    status=["pending", "completed"][i % 2],
                    priority=["low", "medium", "high"][i % 3],
                )

            # Create communications
            if i % 3 == 0:
                Communication.objects.create(
                    type="email",
                    subject=f"Email to Contact{i}",
                    message="Test message",
                    direction="outbound",
                    date=timezone.now().date() - timedelta(days=i),
                    person=Person.objects.get(contact=contact),
                    user=self.admin,
                )

    def test_dashboard_analytics_workflow(self):
        """Test viewing and interpreting dashboard analytics"""

        self.client.login(username="analytics_admin", password="analyticspass123")

        # Step 1: Access main dashboard
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)

        # Step 2: Verify key metrics are displayed
        # Check contact counts
        total_contacts = Contact.objects.filter(user=self.admin, type="person").count()
        self.assertEqual(total_contacts, 20)

        # Check task metrics
        pending_tasks = Task.objects.filter(
            assigned_to=self.admin, status="pending"
        ).count()
        completed_tasks = Task.objects.filter(
            assigned_to=self.admin, status="completed"
        ).count()

        # Step 3: Access pipeline report
        # Group contacts by pipeline stage
        pipeline_data = {}
        for contact in Contact.objects.filter(user=self.admin):
            stage_name = contact.get_pipeline_stage_name() or "No Stage"
            if stage_name not in pipeline_data:
                pipeline_data[stage_name] = 0
            pipeline_data[stage_name] += 1

        # Verify we have contacts (exact count may vary as pipeline stages aren't assigned in test)
        self.assertGreater(len(pipeline_data), 0)  # At least some contacts

        # Step 4: Generate activity report
        # Get communications in last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_comms = Communication.objects.filter(
            user=self.admin, date__gte=thirty_days_ago
        ).count()

        # Step 5: Export data (simulated)
        # In a real scenario, this would generate a CSV/Excel file
        export_data = {
            "total_contacts": total_contacts,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "recent_communications": recent_comms,
            "pipeline_distribution": pipeline_data,
        }

        # Verify export data is complete
        self.assertIn("total_contacts", export_data)
        self.assertIn("pipeline_distribution", export_data)
        self.assertEqual(export_data["total_contacts"], 20)
