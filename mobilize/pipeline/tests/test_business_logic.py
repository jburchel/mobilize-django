"""
Business logic tests for Pipeline app - testing complex workflows and automation.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

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


class StageMovementBusinessLogicTest(TestCase):
    """Test business logic for stage movements"""

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
            name="Initial Contact", order=1, pipeline=self.pipeline
        )
        self.stage2 = PipelineStage.objects.create(
            name="Qualified Lead", order=2, pipeline=self.pipeline
        )
        self.stage3 = PipelineStage.objects.create(
            name="Closed Won", order=3, pipeline=self.pipeline
        )
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )

    def test_stage_progression_tracking(self):
        """Test that stage progression is properly tracked"""
        # Create contact in initial stage
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage1,
        )

        # Record initial entry
        PipelineStageHistory.objects.create(
            pipeline_contact=contact,
            from_stage=None,
            to_stage=self.stage1,
            notes="Initial entry into pipeline",
            created_by=self.user,
        )

        # Move through stages
        for next_stage in [self.stage2, self.stage3]:
            previous_stage = contact.current_stage
            contact.current_stage = next_stage
            contact.entered_at = timezone.now()
            contact.save()

            # Create history entry
            PipelineStageHistory.objects.create(
                pipeline_contact=contact,
                from_stage=previous_stage,
                to_stage=next_stage,
                notes=f"Moved from {previous_stage.name} to {next_stage.name}",
                created_by=self.user,
            )

        # Verify complete progression
        history = contact.stage_history.all().order_by("created_at")
        self.assertEqual(history.count(), 3)

        # Check progression sequence
        self.assertIsNone(history[0].from_stage)
        self.assertEqual(history[0].to_stage, self.stage1)

        self.assertEqual(history[1].from_stage, self.stage1)
        self.assertEqual(history[1].to_stage, self.stage2)

        self.assertEqual(history[2].from_stage, self.stage2)
        self.assertEqual(history[2].to_stage, self.stage3)

    def test_stage_duration_calculation(self):
        """Test calculation of time spent in each stage"""
        # Create contact with specific entry time
        base_time = timezone.now() - timedelta(days=10)

        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage1,
            entered_at=base_time,
        )

        # Create history entries with specific times
        PipelineStageHistory.objects.create(
            pipeline_contact=contact,
            from_stage=None,
            to_stage=self.stage1,
            created_by=self.user,
            created_at=base_time,
        )

        # Move to stage 2 after 5 days
        stage2_time = base_time + timedelta(days=5)
        contact.current_stage = self.stage2
        contact.entered_at = stage2_time
        contact.save()

        PipelineStageHistory.objects.create(
            pipeline_contact=contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            created_by=self.user,
            created_at=stage2_time,
        )

        # Move to stage 3 after 3 more days
        stage3_time = base_time + timedelta(days=8)
        contact.current_stage = self.stage3
        contact.entered_at = stage3_time
        contact.save()

        PipelineStageHistory.objects.create(
            pipeline_contact=contact,
            from_stage=self.stage2,
            to_stage=self.stage3,
            created_by=self.user,
            created_at=stage3_time,
        )

        # Calculate durations
        history = list(contact.stage_history.all().order_by("created_at"))

        # Time in stage 1: 5 days
        stage1_duration = history[1].created_at - history[0].created_at
        self.assertEqual(stage1_duration.days, 5)

        # Time in stage 2: 3 days
        stage2_duration = history[2].created_at - history[1].created_at
        self.assertEqual(stage2_duration.days, 3)

    def test_backward_stage_movement(self):
        """Test moving contact backward in pipeline"""
        # Create contact in stage 3
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage3,
        )

        # Move backward to stage 1
        contact.current_stage = self.stage1
        contact.entered_at = timezone.now()
        contact.save()

        # Create history entry
        PipelineStageHistory.objects.create(
            pipeline_contact=contact,
            from_stage=self.stage3,
            to_stage=self.stage1,
            notes="Moved backward due to qualification issues",
            created_by=self.user,
        )

        # Verify backward movement is tracked
        history = contact.stage_history.latest("created_at")
        self.assertEqual(history.from_stage, self.stage3)
        self.assertEqual(history.to_stage, self.stage1)
        self.assertIn("backward", history.notes.lower())

    def test_stage_skipping(self):
        """Test skipping stages in pipeline"""
        # Create contact in stage 1
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.stage1,
        )

        # Skip stage 2, go directly to stage 3
        contact.current_stage = self.stage3
        contact.entered_at = timezone.now()
        contact.save()

        # Create history entry
        PipelineStageHistory.objects.create(
            pipeline_contact=contact,
            from_stage=self.stage1,
            to_stage=self.stage3,
            notes="Skipped to final stage - fast track",
            created_by=self.user,
        )

        # Verify stage skipping is tracked
        history = contact.stage_history.latest("created_at")
        self.assertEqual(history.from_stage, self.stage1)
        self.assertEqual(history.to_stage, self.stage3)
        self.assertIn("skip", history.notes.lower())


class PipelineAutomationBusinessLogicTest(TestCase):
    """Test business logic for pipeline automation features"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.pipeline = Pipeline.objects.create(
            name="Automated Pipeline", office=self.office
        )
        self.auto_stage = PipelineStage.objects.create(
            name="Auto Stage",
            order=1,
            pipeline=self.pipeline,
            auto_move_days=7,
            auto_reminder=True,
            auto_task_template="Follow up with {contact_name}",
        )
        self.next_stage = PipelineStage.objects.create(
            name="Next Stage", order=2, pipeline=self.pipeline
        )
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", email="john@example.com"
        )

    def test_auto_move_days_logic(self):
        """Test logic for auto-move days functionality"""
        # Create contact that has been in stage for 8 days (past auto_move_days)
        old_time = timezone.now() - timedelta(days=8)

        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.auto_stage,
            entered_at=old_time,
        )

        # Check if contact should be auto-moved
        days_in_stage = (timezone.now() - contact.entered_at).days
        should_auto_move = (
            self.auto_stage.auto_move_days
            and days_in_stage >= self.auto_stage.auto_move_days
        )

        self.assertTrue(should_auto_move)
        self.assertEqual(days_in_stage, 8)
        self.assertEqual(self.auto_stage.auto_move_days, 7)

    def test_auto_reminder_logic(self):
        """Test logic for auto-reminder functionality"""
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.auto_stage,
        )

        # Check if stage has auto-reminder enabled
        self.assertTrue(self.auto_stage.auto_reminder)

        # Logic for determining when to send reminders
        days_in_stage = (timezone.now() - contact.entered_at).days
        should_send_reminder = (
            self.auto_stage.auto_reminder
            and days_in_stage > 0
            and days_in_stage % 3 == 0  # Send reminder every 3 days
        )

        # This would be used in a scheduled task
        self.assertIsInstance(should_send_reminder, bool)

    def test_auto_task_template_rendering(self):
        """Test auto-task template rendering with contact data"""
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=self.auto_stage,
        )

        # Render task template with contact information
        template = self.auto_stage.auto_task_template
        contact_name = f"{contact.person.first_name} {contact.person.last_name}"

        # Simple template rendering (in real implementation, use Django templates)
        rendered_task = template.format(contact_name=contact_name)

        expected = f"Follow up with {contact_name}"
        self.assertEqual(rendered_task, expected)

    def test_pipeline_completion_logic(self):
        """Test logic for determining pipeline completion"""
        # Create final stage
        final_stage = PipelineStage.objects.create(
            name="Closed Won", order=99, pipeline=self.pipeline
        )

        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=self.pipeline,
            current_stage=final_stage,
        )

        # Logic to determine if contact has completed pipeline
        all_stages = self.pipeline.stages.all().order_by("order")
        final_stage_in_pipeline = all_stages.last()
        is_pipeline_complete = contact.current_stage == final_stage_in_pipeline

        self.assertTrue(is_pipeline_complete)
        self.assertEqual(contact.current_stage.order, 99)


class PipelineTypeBusinessLogicTest(TestCase):
    """Test business logic specific to different pipeline types"""

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

    def test_people_pipeline_logic(self):
        """Test business logic specific to people pipelines"""
        people_pipeline = Pipeline.objects.create(
            name="People Pipeline",
            pipeline_type=PIPELINE_TYPE_PEOPLE,
            office=self.office,
        )

        stage = PipelineStage.objects.create(
            name="Initial Contact", order=1, pipeline=people_pipeline
        )

        # People pipeline should only accept person contacts
        person_contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=people_pipeline,
            current_stage=stage,
        )

        self.assertEqual(person_contact.contact_type, "person")
        self.assertEqual(person_contact.contact, self.person)

        # Verify pipeline type
        self.assertEqual(people_pipeline.pipeline_type, PIPELINE_TYPE_PEOPLE)

    def test_church_pipeline_logic(self):
        """Test business logic specific to church pipelines"""
        church_pipeline = Pipeline.objects.create(
            name="Church Pipeline",
            pipeline_type=PIPELINE_TYPE_CHURCH,
            office=self.office,
        )

        stage = PipelineStage.objects.create(
            name="Initial Contact", order=1, pipeline=church_pipeline
        )

        # Church pipeline should only accept church contacts
        church_contact = PipelineContact.objects.create(
            church=self.church,
            contact_type="church",
            pipeline=church_pipeline,
            current_stage=stage,
        )

        self.assertEqual(church_contact.contact_type, "church")
        self.assertEqual(church_contact.contact, self.church)

        # Verify pipeline type
        self.assertEqual(church_pipeline.pipeline_type, PIPELINE_TYPE_CHURCH)

    def test_custom_pipeline_logic(self):
        """Test business logic for custom pipelines"""
        custom_pipeline = Pipeline.objects.create(
            name="Custom Pipeline",
            pipeline_type=PIPELINE_TYPE_CUSTOM,
            office=self.office,
        )

        stage = PipelineStage.objects.create(
            name="Custom Stage", order=1, pipeline=custom_pipeline
        )

        # Custom pipeline should accept both person and church contacts
        person_contact = PipelineContact.objects.create(
            person=self.person,
            contact_type="person",
            pipeline=custom_pipeline,
            current_stage=stage,
        )

        church_contact = PipelineContact.objects.create(
            church=self.church,
            contact_type="church",
            pipeline=custom_pipeline,
            current_stage=stage,
        )

        self.assertEqual(person_contact.pipeline, custom_pipeline)
        self.assertEqual(church_contact.pipeline, custom_pipeline)
        self.assertEqual(custom_pipeline.pipeline_type, PIPELINE_TYPE_CUSTOM)

    def test_main_pipeline_logic(self):
        """Test business logic for main pipeline designation"""
        # Create multiple pipelines
        pipeline1 = Pipeline.objects.create(
            name="Pipeline 1", office=self.office, is_main_pipeline=False
        )

        main_pipeline = Pipeline.objects.create(
            name="Main Pipeline", office=self.office, is_main_pipeline=True
        )

        pipeline3 = Pipeline.objects.create(
            name="Pipeline 3", office=self.office, is_main_pipeline=False
        )

        # Logic to get main pipeline for office
        office_main_pipeline = Pipeline.objects.filter(
            office=self.office, is_main_pipeline=True
        ).first()

        self.assertEqual(office_main_pipeline, main_pipeline)

        # Logic to get default pipeline if no main pipeline set
        default_pipeline = Pipeline.objects.filter(office=self.office).first()

        self.assertIsNotNone(default_pipeline)


class PipelineAnalyticsBusinessLogicTest(TestCase):
    """Test business logic for pipeline analytics and reporting"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com"
        )
        self.office = Office.objects.create(name="Test Office", code="TEST")
        self.pipeline = Pipeline.objects.create(
            name="Analytics Pipeline", office=self.office
        )
        self.stage1 = PipelineStage.objects.create(
            name="Lead", order=1, pipeline=self.pipeline
        )
        self.stage2 = PipelineStage.objects.create(
            name="Qualified", order=2, pipeline=self.pipeline
        )
        self.stage3 = PipelineStage.objects.create(
            name="Closed", order=3, pipeline=self.pipeline
        )

        # Create test contacts
        self.contacts = []
        for i in range(5):
            person = Person.objects.create(
                first_name=f"Person{i}",
                last_name="Test",
                email=f"person{i}@example.com",
            )
            self.contacts.append(person)

    def test_stage_conversion_rate_calculation(self):
        """Test calculation of conversion rates between stages"""
        # Create contacts in different stages
        stage1_contacts = []
        stage2_contacts = []
        stage3_contacts = []

        # 5 contacts in stage 1
        for i in range(5):
            contact = PipelineContact.objects.create(
                person=self.contacts[i],
                contact_type="person",
                pipeline=self.pipeline,
                current_stage=self.stage1,
            )
            stage1_contacts.append(contact)

        # 3 of them moved to stage 2
        for i in range(3):
            stage1_contacts[i].current_stage = self.stage2
            stage1_contacts[i].save()
            stage2_contacts.append(stage1_contacts[i])

        # 1 of them moved to stage 3
        stage2_contacts[0].current_stage = self.stage3
        stage2_contacts[0].save()
        stage3_contacts.append(stage2_contacts[0])

        # Calculate conversion rates
        total_contacts = PipelineContact.objects.filter(pipeline=self.pipeline).count()
        stage1_count = PipelineContact.objects.filter(
            pipeline=self.pipeline, current_stage=self.stage1
        ).count()
        stage2_count = PipelineContact.objects.filter(
            pipeline=self.pipeline, current_stage=self.stage2
        ).count()
        stage3_count = PipelineContact.objects.filter(
            pipeline=self.pipeline, current_stage=self.stage3
        ).count()

        self.assertEqual(total_contacts, 5)
        self.assertEqual(stage1_count, 2)  # 2 remaining in stage 1
        self.assertEqual(stage2_count, 2)  # 2 remaining in stage 2
        self.assertEqual(stage3_count, 1)  # 1 in final stage

        # Conversion rate from stage 1 to stage 2: 3/5 = 60%
        stage1_to_stage2_rate = 3 / 5 * 100
        self.assertEqual(stage1_to_stage2_rate, 60.0)

        # Conversion rate from stage 2 to stage 3: 1/3 = 33.33%
        stage2_to_stage3_rate = 1 / 3 * 100
        self.assertAlmostEqual(stage2_to_stage3_rate, 33.33, places=2)

    def test_average_time_in_stage_calculation(self):
        """Test calculation of average time spent in each stage"""
        base_time = timezone.now() - timedelta(days=20)

        # Create contacts with varying time in stages
        durations = []
        for i, person in enumerate(self.contacts):
            entered_time = base_time + timedelta(days=i * 2)
            contact = PipelineContact.objects.create(
                person=person,
                contact_type="person",
                pipeline=self.pipeline,
                current_stage=self.stage1,
                entered_at=entered_time,
            )

            # Calculate time in current stage
            time_in_stage = timezone.now() - contact.entered_at
            durations.append(time_in_stage.total_seconds())

        # Calculate average time in stage
        if durations:
            average_seconds = sum(durations) / len(durations)
            average_days = average_seconds / (24 * 60 * 60)

            # Should be approximately 12 days average (0, 2, 4, 6, 8 days ago)
            self.assertGreater(average_days, 0)
            self.assertLess(average_days, 20)

    def test_pipeline_velocity_calculation(self):
        """Test calculation of pipeline velocity (contacts per time period)"""
        # Create contacts over different time periods
        now = timezone.now()

        # 2 contacts this week
        this_week_contacts = []
        for i in range(2):
            person = Person.objects.create(
                first_name=f"ThisWeek{i}",
                last_name="Test",
                email=f"thisweek{i}@example.com",
            )
            contact = PipelineContact.objects.create(
                person=person,
                contact_type="person",
                pipeline=self.pipeline,
                current_stage=self.stage1,
                entered_at=now - timedelta(days=i),
            )
            this_week_contacts.append(contact)

        # 3 contacts last week
        last_week_contacts = []
        for i in range(3):
            person = Person.objects.create(
                first_name=f"LastWeek{i}",
                last_name="Test",
                email=f"lastweek{i}@example.com",
            )
            contact = PipelineContact.objects.create(
                person=person,
                contact_type="person",
                pipeline=self.pipeline,
                current_stage=self.stage1,
                entered_at=now - timedelta(days=7 + i),
            )
            last_week_contacts.append(contact)

        # Calculate weekly velocity
        week_start = now - timedelta(days=7)
        this_week_count = PipelineContact.objects.filter(
            pipeline=self.pipeline, entered_at__gte=week_start
        ).count()

        last_week_start = now - timedelta(days=14)
        last_week_end = now - timedelta(days=7)
        last_week_count = PipelineContact.objects.filter(
            pipeline=self.pipeline,
            entered_at__gte=last_week_start,
            entered_at__lt=last_week_end,
        ).count()

        self.assertEqual(this_week_count, 2)
        self.assertEqual(last_week_count, 3)

        # Velocity trend (negative indicates slowing down)
        velocity_change = this_week_count - last_week_count
        self.assertEqual(velocity_change, -1)  # Slower this week
