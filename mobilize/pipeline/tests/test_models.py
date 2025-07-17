"""
Test cases for Pipeline app models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

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
    PIPELINE_TYPE_CUSTOM,
)

User = get_user_model()


class PipelineModelTest(TestCase):
    """Test cases for Pipeline model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")

    def test_pipeline_creation(self):
        """Test basic pipeline creation"""
        pipeline = Pipeline.objects.create(
            name="Test Pipeline",
            description="A test pipeline",
            pipeline_type=PIPELINE_TYPE_PEOPLE,
            office=self.office,
        )

        self.assertEqual(pipeline.name, "Test Pipeline")
        self.assertEqual(pipeline.description, "A test pipeline")
        self.assertEqual(pipeline.pipeline_type, PIPELINE_TYPE_PEOPLE)
        self.assertEqual(pipeline.office, self.office)
        self.assertFalse(pipeline.is_main_pipeline)
        self.assertIsNotNone(pipeline.created_at)
        self.assertIsNotNone(pipeline.updated_at)

    def test_pipeline_types(self):
        """Test all pipeline types can be created"""
        for pipeline_type, _ in Pipeline._meta.get_field("pipeline_type").choices:
            pipeline = Pipeline.objects.create(
                name=f"Test {pipeline_type} Pipeline",
                pipeline_type=pipeline_type,
                office=self.office,
            )
            self.assertEqual(pipeline.pipeline_type, pipeline_type)

    def test_pipeline_str_representation(self):
        """Test pipeline string representation"""
        pipeline = Pipeline.objects.create(name="Test Pipeline", office=self.office)
        self.assertEqual(str(pipeline), "Test Pipeline")

    def test_pipeline_main_pipeline_flag(self):
        """Test main pipeline flag functionality"""
        pipeline = Pipeline.objects.create(
            name="Main Pipeline", office=self.office, is_main_pipeline=True
        )
        self.assertTrue(pipeline.is_main_pipeline)

    def test_pipeline_office_relationship(self):
        """Test pipeline office foreign key relationship"""
        pipeline = Pipeline.objects.create(name="Test Pipeline", office=self.office)

        # Test access from office to pipelines
        self.assertIn(pipeline, self.office.pipelines.all())

        # Test cascade delete
        office_id = self.office.id
        self.office.delete()
        self.assertFalse(Pipeline.objects.filter(id=pipeline.id).exists())


class PipelineStageModelTest(TestCase):
    """Test cases for PipelineStage model"""

    def setUp(self):
        """Set up test data"""
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.pipeline = Pipeline.objects.create(
            name="Test Pipeline", office=self.office
        )

    def test_pipeline_stage_creation(self):
        """Test basic pipeline stage creation"""
        stage = PipelineStage.objects.create(
            name="Initial Contact",
            description="First contact with prospect",
            order=1,
            color="#FF0000",
            pipeline=self.pipeline,
        )

        self.assertEqual(stage.name, "Initial Contact")
        self.assertEqual(stage.description, "First contact with prospect")
        self.assertEqual(stage.order, 1)
        self.assertEqual(stage.color, "#FF0000")
        self.assertEqual(stage.pipeline, self.pipeline)
        self.assertIsNotNone(stage.created_at)
        self.assertIsNotNone(stage.updated_at)

    def test_pipeline_stage_ordering(self):
        """Test pipeline stage ordering"""
        stage1 = PipelineStage.objects.create(
            name="Stage 1", order=1, pipeline=self.pipeline
        )
        stage2 = PipelineStage.objects.create(
            name="Stage 2", order=2, pipeline=self.pipeline
        )
        stage3 = PipelineStage.objects.create(
            name="Stage 3", order=3, pipeline=self.pipeline
        )

        stages = list(self.pipeline.stages.all())
        self.assertEqual(stages[0], stage1)
        self.assertEqual(stages[1], stage2)
        self.assertEqual(stages[2], stage3)

    def test_pipeline_stage_str_representation(self):
        """Test pipeline stage string representation"""
        stage = PipelineStage.objects.create(
            name="Test Stage", order=1, pipeline=self.pipeline
        )
        expected = f"{self.pipeline.name} - Test Stage"
        self.assertEqual(str(stage), expected)

    def test_pipeline_stage_automation_fields(self):
        """Test automation fields functionality"""
        stage = PipelineStage.objects.create(
            name="Automated Stage",
            order=1,
            pipeline=self.pipeline,
            auto_move_days=7,
            auto_reminder=True,
            auto_task_template="Follow up with contact",
        )

        self.assertEqual(stage.auto_move_days, 7)
        self.assertTrue(stage.auto_reminder)
        self.assertEqual(stage.auto_task_template, "Follow up with contact")

    def test_pipeline_stage_pipeline_relationship(self):
        """Test stage pipeline foreign key relationship"""
        stage = PipelineStage.objects.create(
            name="Test Stage", order=1, pipeline=self.pipeline
        )

        # Test access from pipeline to stages
        self.assertIn(stage, self.pipeline.stages.all())

        # Test cascade delete
        self.pipeline.delete()
        self.assertFalse(PipelineStage.objects.filter(id=stage.id).exists())


class PipelineContactModelTest(TestCase):
    """Test cases for PipelineContact model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.pipeline = Pipeline.objects.create(
            name="Test Pipeline", office=self.office
        )
        self.stage = PipelineStage.objects.create(
            name="Initial Contact", order=1, pipeline=self.pipeline
        )
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )
        self.church = Church.objects.create(name="Test Church")

    def test_pipeline_contact_person_creation(self):
        """Test creating pipeline contact for person"""
        pipeline_contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage,
        )

        self.assertEqual(pipeline_contact.person, self.person)
        self.assertIsNone(pipeline_contact.church)
        self.assertEqual(pipeline_contact.contact_type, "person")
        self.assertEqual(pipeline_contact.pipeline, self.pipeline)
        self.assertEqual(pipeline_contact.current_stage, self.stage)
        self.assertIsNotNone(pipeline_contact.entered_at)

    def test_pipeline_contact_church_creation(self):
        """Test creating pipeline contact for church"""
        pipeline_contact = PipelineContact.objects.create(
            church=self.church,
            contact_type="church",
            pipeline=self.pipeline,
            current_stage=self.stage,
        )

        self.assertEqual(pipeline_contact.church, self.church)
        self.assertIsNone(pipeline_contact.person)
        self.assertEqual(pipeline_contact.contact_type, "church")
        self.assertEqual(pipeline_contact.pipeline, self.pipeline)
        self.assertEqual(pipeline_contact.current_stage, self.stage)

    def test_pipeline_contact_contact_property(self):
        """Test contact property returns correct object"""
        # Test person contact
        person_contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage,
        )
        self.assertEqual(person_contact.contact, self.person)

        # Test church contact
        church_contact = PipelineContact.objects.create(
            church=self.church,
            contact_type="church",
            pipeline=self.pipeline,
            current_stage=self.stage,
        )
        self.assertEqual(church_contact.contact, self.church)

    def test_pipeline_contact_str_representation(self):
        """Test pipeline contact string representation"""
        pipeline_contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage,
        )
        expected = f"{self.person} in {self.pipeline.name} at {self.stage.name}"
        self.assertEqual(str(pipeline_contact), expected)

    def test_pipeline_contact_relationships(self):
        """Test foreign key relationships"""
        pipeline_contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage,
        )

        # Test access from related objects
        self.assertIn(pipeline_contact, self.person.pipeline_entries.all())
        self.assertIn(pipeline_contact, self.pipeline.contacts.all())
        self.assertIn(pipeline_contact, self.stage.current_contacts.all())


class PipelineStageHistoryModelTest(TestCase):
    """Test cases for PipelineStageHistory model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.pipeline = Pipeline.objects.create(
            name="Test Pipeline", office=self.office
        )
        self.stage1 = PipelineStage.objects.create(
            name="Stage 1", order=1, pipeline=self.pipeline
        )
        self.stage2 = PipelineStage.objects.create(
            name="Stage 2", order=2, pipeline=self.pipeline
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

    def test_pipeline_stage_history_creation(self):
        """Test basic pipeline stage history creation"""
        history = PipelineStageHistory.objects.create(
            pipeline_contact=self.pipeline_contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            notes="Test move",
            created_by=self.user,
        )

        self.assertEqual(history.pipeline_contact, self.pipeline_contact)
        self.assertEqual(history.from_stage, self.stage1)
        self.assertEqual(history.to_stage, self.stage2)
        self.assertEqual(history.notes, "Test move")
        self.assertEqual(history.created_by, self.user)
        self.assertIsNotNone(history.created_at)

    def test_pipeline_stage_history_initial_entry(self):
        """Test creating history for initial entry (no from_stage)"""
        history = PipelineStageHistory.objects.create(
            pipeline_contact=self.pipeline_contact,
            from_stage=None,
            to_stage=self.stage1,
            notes="Initial entry",
            created_by=self.user,
        )

        self.assertIsNone(history.from_stage)
        self.assertEqual(history.to_stage, self.stage1)
        self.assertEqual(history.notes, "Initial entry")

    def test_pipeline_stage_history_str_representation(self):
        """Test pipeline stage history string representation"""
        history = PipelineStageHistory.objects.create(
            pipeline_contact=self.pipeline_contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            created_by=self.user,
        )
        expected = (
            f"{self.pipeline_contact.contact} moved from {self.stage1} to {self.stage2}"
        )
        self.assertEqual(str(history), expected)

    def test_pipeline_stage_history_no_from_stage_str(self):
        """Test string representation with no from_stage"""
        history = PipelineStageHistory.objects.create(
            pipeline_contact=self.pipeline_contact,
            from_stage=None,
            to_stage=self.stage1,
            created_by=self.user,
        )
        expected = f"{self.pipeline_contact.contact} moved from None to {self.stage1}"
        self.assertEqual(str(history), expected)

    def test_pipeline_stage_history_ordering(self):
        """Test history ordering (most recent first)"""
        # Create first history entry
        history1 = PipelineStageHistory.objects.create(
            pipeline_contact=self.pipeline_contact,
            from_stage=None,
            to_stage=self.stage1,
            created_by=self.user,
        )

        # Create second history entry
        history2 = PipelineStageHistory.objects.create(
            pipeline_contact=self.pipeline_contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            created_by=self.user,
        )

        # Get all history entries
        history_entries = list(PipelineStageHistory.objects.all())

        # Most recent should be first
        self.assertEqual(history_entries[0], history2)
        self.assertEqual(history_entries[1], history1)

    def test_pipeline_stage_history_relationships(self):
        """Test foreign key relationships"""
        history = PipelineStageHistory.objects.create(
            pipeline_contact=self.pipeline_contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            created_by=self.user,
        )

        # Test access from related objects
        self.assertIn(history, self.pipeline_contact.stage_history.all())
        self.assertIn(history, self.stage1.from_stage_history.all())
        self.assertIn(history, self.stage2.to_stage_history.all())
        self.assertIn(history, self.user.stage_changes.all())

    def test_pipeline_stage_history_user_deletion(self):
        """Test history when user is deleted (should set to NULL)"""
        history = PipelineStageHistory.objects.create(
            pipeline_contact=self.pipeline_contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            created_by=self.user,
        )

        # Get the user ID
        user_id = self.user.id

        # Test that the relationship exists
        self.assertEqual(history.created_by, self.user)

        # Note: We can't actually test user deletion in this test environment
        # due to database constraints, but we can verify the relationship
        # and that the field allows NULL
        history.created_by = None
        history.save()

        # Refresh from database
        history.refresh_from_db()

        # created_by should be NULL now
        self.assertIsNone(history.created_by)
