"""
Test cases for Pipeline app views.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone

from mobilize.admin_panel.models import Office
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.pipeline.models import (
    Pipeline,
    PipelineStage,
    PipelineContact,
    PipelineStageHistory,
    PIPELINE_TYPE_PEOPLE,
    PIPELINE_TYPE_CHURCH,
)

User = get_user_model()


class PipelineVisualizationViewTest(TestCase):
    """Test cases for pipeline_visualization view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.pipeline = Pipeline.objects.create(
            name="Test Pipeline",
            pipeline_type=PIPELINE_TYPE_PEOPLE,
            office=self.office,
            is_main_pipeline=True,
        )
        self.stage1 = PipelineStage.objects.create(
            name="Initial Contact", order=1, pipeline=self.pipeline, color="#FF0000"
        )
        self.stage2 = PipelineStage.objects.create(
            name="Follow Up", order=2, pipeline=self.pipeline, color="#00FF00"
        )
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )
        self.pipeline_contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage1,
        )

    def test_pipeline_visualization_requires_login(self):
        """Test that pipeline visualization requires authentication"""
        url = reverse("pipeline:pipeline_visualization_default")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_pipeline_visualization_with_pipeline_id(self):
        """Test pipeline visualization with specific pipeline ID"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "pipeline:pipeline_visualization", kwargs={"pipeline_id": self.pipeline.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pipeline.name)
        self.assertContains(response, self.stage1.name)
        self.assertContains(response, self.stage2.name)
        self.assertContains(response, self.person.first_name)

    def test_pipeline_visualization_default(self):
        """Test pipeline visualization without pipeline ID (default)"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("pipeline:pipeline_visualization_default")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Should show the first available pipeline
        self.assertContains(response, self.pipeline.name)

    def test_pipeline_visualization_context_data(self):
        """Test that context contains correct data"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "pipeline:pipeline_visualization", kwargs={"pipeline_id": self.pipeline.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.context["pipeline"], self.pipeline)
        self.assertIn("stages_with_contacts", response.context)
        self.assertIn("all_pipelines", response.context)

        # Check stages_with_contacts structure
        stages_with_contacts = response.context["stages_with_contacts"]
        self.assertEqual(len(stages_with_contacts), 2)  # Two stages

        # Check first stage has the contact
        stage1_data = stages_with_contacts[0]
        self.assertEqual(stage1_data["stage"], self.stage1)
        self.assertIn(self.pipeline_contact, stage1_data["contacts"])

        # Check second stage is empty
        stage2_data = stages_with_contacts[1]
        self.assertEqual(stage2_data["stage"], self.stage2)
        self.assertEqual(stage2_data["contacts"].count(), 0)

    def test_pipeline_visualization_nonexistent_pipeline(self):
        """Test pipeline visualization with nonexistent pipeline ID"""
        self.client.login(username="testuser", password="testpass123")
        url = reverse("pipeline:pipeline_visualization", kwargs={"pipeline_id": 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_pipeline_visualization_empty_pipeline(self):
        """Test pipeline visualization with empty pipeline"""
        empty_pipeline = Pipeline.objects.create(
            name="Empty Pipeline", office=self.office
        )
        empty_stage = PipelineStage.objects.create(
            name="Empty Stage", order=1, pipeline=empty_pipeline
        )

        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "pipeline:pipeline_visualization", kwargs={"pipeline_id": empty_pipeline.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, empty_pipeline.name)
        self.assertContains(response, empty_stage.name)

        # Check that stages have no contacts
        stages_with_contacts = response.context["stages_with_contacts"]
        self.assertEqual(len(stages_with_contacts), 1)
        self.assertEqual(stages_with_contacts[0]["contacts"].count(), 0)

    def test_pipeline_visualization_duration_calculation(self):
        """Test that average duration calculation works"""
        # Add another contact to the same stage
        person2 = Person.objects.create(
            first_name="Jane", last_name="Smith", email="jane@example.com"
        )
        pipeline_contact2 = PipelineContact.objects.create(
            person=person2,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage1,
            entered_at=timezone.now() - timezone.timedelta(days=5),
        )

        self.client.login(username="testuser", password="testpass123")
        url = reverse(
            "pipeline:pipeline_visualization", kwargs={"pipeline_id": self.pipeline.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        stages_with_contacts = response.context["stages_with_contacts"]
        stage1_data = stages_with_contacts[0]

        # Should have calculated average duration
        self.assertIsNotNone(stage1_data["average_duration"])


class MovePipelineContactViewTest(TestCase):
    """Test cases for move_pipeline_contact view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.pipeline = Pipeline.objects.create(
            name="Test Pipeline", office=self.office
        )
        self.stage1 = PipelineStage.objects.create(
            name="Initial Contact", order=1, pipeline=self.pipeline
        )
        self.stage2 = PipelineStage.objects.create(
            name="Follow Up", order=2, pipeline=self.pipeline
        )
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )
        self.pipeline_contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage1,
        )
        self.url = reverse("pipeline:move_contact")

    def test_move_contact_requires_login(self):
        """Test that moving contact requires authentication"""
        response = self.client.post(
            self.url,
            {
                "pipeline_contact_id": self.pipeline_contact.id,
                "target_stage_id": self.stage2.id,
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_move_contact_requires_post(self):
        """Test that moving contact requires POST method"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_successful_contact_move(self):
        """Test successful contact movement between stages"""
        self.client.login(username="testuser", password="testpass123")

        # Record initial stage
        initial_stage = self.pipeline_contact.current_stage

        response = self.client.post(
            self.url,
            {
                "pipeline_contact_id": self.pipeline_contact.id,
                "target_stage_id": self.stage2.id,
            },
        )

        # Should redirect to pipeline visualization
        expected_url = reverse(
            "pipeline:pipeline_visualization", kwargs={"pipeline_id": self.pipeline.id}
        )
        self.assertRedirects(response, expected_url)

        # Refresh contact from database
        self.pipeline_contact.refresh_from_db()

        # Contact should be in new stage
        self.assertEqual(self.pipeline_contact.current_stage, self.stage2)

        # Check that history was created
        history = PipelineStageHistory.objects.filter(
            pipeline_contact=self.pipeline_contact
        ).latest("created_at")

        self.assertEqual(history.from_stage, initial_stage)
        self.assertEqual(history.to_stage, self.stage2)
        self.assertEqual(history.created_by, self.user)
        self.assertIsNotNone(history.notes)

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("moved to" in str(msg) for msg in messages))

    def test_move_contact_missing_contact_id(self):
        """Test moving contact with missing contact ID"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(self.url, {"target_stage_id": self.stage2.id})

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Missing contact" in str(msg) for msg in messages))

    def test_move_contact_missing_stage_id(self):
        """Test moving contact with missing target stage ID"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            self.url, {"pipeline_contact_id": self.pipeline_contact.id}
        )

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Missing contact" in str(msg) for msg in messages))

    def test_move_contact_nonexistent_contact(self):
        """Test moving nonexistent contact"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            self.url, {"pipeline_contact_id": 99999, "target_stage_id": self.stage2.id}
        )

        self.assertEqual(response.status_code, 404)

    def test_move_contact_nonexistent_stage(self):
        """Test moving contact to nonexistent stage"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            self.url,
            {"pipeline_contact_id": self.pipeline_contact.id, "target_stage_id": 99999},
        )

        self.assertEqual(response.status_code, 404)

    def test_move_contact_to_same_stage(self):
        """Test moving contact to the same stage"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            self.url,
            {
                "pipeline_contact_id": self.pipeline_contact.id,
                "target_stage_id": self.stage1.id,  # Same as current stage
            },
        )

        # Should redirect to pipeline visualization
        expected_url = reverse(
            "pipeline:pipeline_visualization", kwargs={"pipeline_id": self.pipeline.id}
        )
        self.assertRedirects(response, expected_url)

        # Check info message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already in" in str(msg) for msg in messages))

        # No new history should be created
        history_count = PipelineStageHistory.objects.filter(
            pipeline_contact=self.pipeline_contact
        ).count()
        self.assertEqual(history_count, 0)

    def test_move_contact_wrong_pipeline_stage(self):
        """Test moving contact to stage from different pipeline"""
        # Create different pipeline and stage
        other_pipeline = Pipeline.objects.create(
            name="Other Pipeline", office=self.office
        )
        other_stage = PipelineStage.objects.create(
            name="Other Stage", order=1, pipeline=other_pipeline
        )

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            self.url,
            {
                "pipeline_contact_id": self.pipeline_contact.id,
                "target_stage_id": other_stage.id,
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_move_church_contact(self):
        """Test moving church contact between stages"""
        church = Church.objects.create(name="Test Church")
        church_contact = PipelineContact.objects.create(
            church=church,
            contact_type="church",
            pipeline=self.pipeline,
            current_stage=self.stage1,
        )

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            self.url,
            {
                "pipeline_contact_id": church_contact.id,
                "target_stage_id": self.stage2.id,
            },
        )

        # Should redirect to pipeline visualization
        expected_url = reverse(
            "pipeline:pipeline_visualization", kwargs={"pipeline_id": self.pipeline.id}
        )
        self.assertRedirects(response, expected_url)

        # Refresh contact from database
        church_contact.refresh_from_db()

        # Contact should be in new stage
        self.assertEqual(church_contact.current_stage, self.stage2)

        # Check that history was created
        history = PipelineStageHistory.objects.filter(
            pipeline_contact=church_contact
        ).latest("created_at")

        self.assertEqual(history.from_stage, self.stage1)
        self.assertEqual(history.to_stage, self.stage2)
        self.assertEqual(history.created_by, self.user)

    def test_move_contact_updates_entered_at(self):
        """Test that moving contact updates entered_at timestamp"""
        self.client.login(username="testuser", password="testpass123")

        # Record original entered_at time
        original_entered_at = self.pipeline_contact.entered_at

        # Wait a moment to ensure timestamp difference
        import time

        time.sleep(0.1)

        response = self.client.post(
            self.url,
            {
                "pipeline_contact_id": self.pipeline_contact.id,
                "target_stage_id": self.stage2.id,
            },
        )

        # Refresh contact from database
        self.pipeline_contact.refresh_from_db()

        # entered_at should be updated
        self.assertNotEqual(self.pipeline_contact.entered_at, original_entered_at)
        self.assertIsNotNone(self.pipeline_contact.entered_at)
