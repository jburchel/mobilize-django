"""
Tests for communications app
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from mobilize.communications.models import Communication, EmailTemplate, EmailSignature
from mobilize.contacts.models import Person

User = get_user_model()


class CommunicationModelTests(TestCase):
    """Test cases for Communication model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )

        self.contact = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )

    def test_create_communication(self):
        """Test creating a communication record"""
        communication = Communication.objects.create(
            subject="Test Email",
            message="This is a test email",
            type="email",
            direction="outbound",
            person=self.contact,
        )

        self.assertEqual(communication.subject, "Test Email")
        self.assertEqual(communication.message, "This is a test email")
        self.assertEqual(communication.type, "email")
        self.assertEqual(communication.direction, "outbound")
        self.assertEqual(communication.person, self.contact)
        self.assertIsNotNone(communication.created_at)

    def test_communication_string_representation(self):
        """Test communication string representation"""
        communication = Communication.objects.create(
            subject="Test Subject",
            type="email",
            direction="outbound",
            person=self.contact,
        )

        self.assertEqual(str(communication), "Test Subject")

    def test_communication_types(self):
        """Test different communication types"""
        types = ["email", "phone", "text", "meeting"]

        for comm_type in types:
            communication = Communication.objects.create(
                subject=f"Test {comm_type}",
                type=comm_type,
                direction="outbound",
                person=self.contact,
            )
            self.assertEqual(communication.type, comm_type)

    def test_communication_directions(self):
        """Test communication directions"""
        directions = ["inbound", "outbound"]

        for direction in directions:
            communication = Communication.objects.create(
                subject=f"Test {direction}",
                type="email",
                direction=direction,
                person=self.contact,
            )
            self.assertEqual(communication.direction, direction)


class EmailTemplateModelTests(TestCase):
    """Test cases for EmailTemplate model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )

    def test_create_email_template(self):
        """Test creating an email template"""
        template = EmailTemplate.objects.create(
            name="Welcome Email",
            subject="Welcome to our service",
            body="Thank you for joining us, {{first_name}}!",
            created_by=self.user,
        )

        self.assertEqual(template.name, "Welcome Email")
        self.assertEqual(template.subject, "Welcome to our service")
        self.assertIn("{{first_name}}", template.body)
        self.assertEqual(template.created_by, self.user)
        self.assertTrue(template.is_active)

    def test_template_string_representation(self):
        """Test template string representation"""
        template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test Subject",
            body="Test Body",
            created_by=self.user,
        )

        self.assertEqual(str(template), "Test Template")

    def test_template_deactivation(self):
        """Test template deactivation"""
        template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test Subject",
            body="Test Body",
            created_by=self.user,
        )

        # Should be active by default
        self.assertTrue(template.is_active)

        # Deactivate template
        template.is_active = False
        template.save()

        self.assertFalse(template.is_active)


class EmailSignatureModelTests(TestCase):
    """Test cases for EmailSignature model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )

    def test_create_email_signature(self):
        """Test creating an email signature"""
        signature = EmailSignature.objects.create(
            name="Professional Signature",
            content="Best regards,\nTest User\ntest@example.com",
            user=self.user,
        )

        self.assertEqual(signature.name, "Professional Signature")
        self.assertIn("Test User", signature.content)
        self.assertIn("test@example.com", signature.content)
        self.assertEqual(signature.user, self.user)
        self.assertTrue(signature.is_default)  # Should be default as first signature

    def test_signature_string_representation(self):
        """Test signature string representation"""
        signature = EmailSignature.objects.create(
            name="Test Signature", content="Test content", user=self.user
        )

        expected = f"{self.user.get_full_name()} - Test Signature"
        self.assertEqual(str(signature), expected)

    def test_default_signature(self):
        """Test setting default signature"""
        signature1 = EmailSignature.objects.create(
            name="Signature 1", content="Content 1", user=self.user, is_default=True
        )

        signature2 = EmailSignature.objects.create(
            name="Signature 2", content="Content 2", user=self.user, is_default=True
        )

        # Refresh from database
        signature1.refresh_from_db()
        signature2.refresh_from_db()

        # Only the second signature should be default
        self.assertFalse(signature1.is_default)
        self.assertTrue(signature2.is_default)

        # Both signatures should exist
        self.assertEqual(EmailSignature.objects.filter(user=self.user).count(), 2)


class CommunicationViewTests(TestCase):
    """Test cases for communication views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.contact = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )

        self.communication = Communication.objects.create(
            subject="Test Communication",
            message="Test message",
            type="email",
            direction="outbound",
            person=self.contact,
        )

    def test_communication_list_requires_login(self):
        """Test that communication list requires authentication"""
        url = reverse("communications:communication_list")
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_communication_list_view(self):
        """Test communication list view"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("communications:communication_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Communication")
        self.assertContains(response, self.communication.subject)

    def test_communication_detail_view(self):
        """Test communication detail view"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "communications:communication_detail", kwargs={"pk": self.communication.pk}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.communication.subject)
        self.assertContains(response, self.communication.message)

    def test_send_email_view_get(self):
        """Test send email form"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("communications:send_email")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send Email")

    def test_compose_email_view(self):
        """Test compose email view"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("communications:compose_email")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compose Email")


class EmailTemplateViewTests(TestCase):
    """Test cases for email template views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test Subject",
            body="Test Body",
            created_by=self.user,
        )

    def test_template_list_view(self):
        """Test email template list view"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("communications:email_template_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email Templates")
        self.assertContains(response, self.template.name)

    def test_template_create_view(self):
        """Test email template creation"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("communications:email_template_create")

        template_data = {
            "name": "New Template",
            "subject": "New Subject",
            "body": "New template body with {{first_name}} placeholder",
        }

        response = self.client.post(url, template_data)

        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)

        # Check template was created
        new_template = EmailTemplate.objects.filter(name="New Template").first()
        self.assertIsNotNone(new_template)
        self.assertEqual(new_template.created_by, self.user)
