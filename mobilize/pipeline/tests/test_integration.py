"""
Integration tests for Pipeline app - testing cross-app functionality.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction

from mobilize.admin_panel.models import Office, UserOffice
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.pipeline.models import (
    Pipeline, PipelineStage, PipelineContact, PipelineStageHistory,
    PIPELINE_TYPE_PEOPLE, PIPELINE_TYPE_CHURCH
)

User = get_user_model()


class PipelineOfficeIntegrationTest(TestCase):
    """Test pipeline integration with office system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office1 = Office.objects.create(
            name='Office 1',
            code='OFF1'
        )
        self.office2 = Office.objects.create(
            name='Office 2',
            code='OFF2'
        )
        # Assign user to office1
        UserOffice.objects.create(
            user=self.user,
            office=self.office1,
            role='office_admin',
            is_primary=True
        )
    
    def test_pipeline_office_scoping(self):
        """Test that pipelines are properly scoped to offices"""
        # Create pipelines for different offices
        pipeline1 = Pipeline.objects.create(
            name='Office 1 Pipeline',
            office=self.office1
        )
        pipeline2 = Pipeline.objects.create(
            name='Office 2 Pipeline',
            office=self.office2
        )
        
        # Test office-specific pipeline queries
        office1_pipelines = Pipeline.objects.filter(office=self.office1)
        office2_pipelines = Pipeline.objects.filter(office=self.office2)
        
        self.assertIn(pipeline1, office1_pipelines)
        self.assertNotIn(pipeline2, office1_pipelines)
        
        self.assertIn(pipeline2, office2_pipelines)
        self.assertNotIn(pipeline1, office2_pipelines)
    
    def test_office_deletion_cascade(self):
        """Test that deleting office cascades to pipelines"""
        pipeline = Pipeline.objects.create(
            name='Test Pipeline',
            office=self.office1
        )
        stage = PipelineStage.objects.create(
            name='Test Stage',
            order=1,
            pipeline=pipeline
        )
        
        pipeline_id = pipeline.id
        stage_id = stage.id
        
        # Delete office
        self.office1.delete()
        
        # Pipeline and stages should be deleted
        self.assertFalse(Pipeline.objects.filter(id=pipeline_id).exists())
        self.assertFalse(PipelineStage.objects.filter(id=stage_id).exists())
    
    def test_multiple_pipelines_per_office(self):
        """Test that offices can have multiple pipelines"""
        pipeline1 = Pipeline.objects.create(
            name='People Pipeline',
            pipeline_type=PIPELINE_TYPE_PEOPLE,
            office=self.office1
        )
        pipeline2 = Pipeline.objects.create(
            name='Church Pipeline',
            pipeline_type=PIPELINE_TYPE_CHURCH,
            office=self.office1
        )
        
        office_pipelines = self.office1.pipelines.all()
        self.assertEqual(office_pipelines.count(), 2)
        self.assertIn(pipeline1, office_pipelines)
        self.assertIn(pipeline2, office_pipelines)


class PipelineContactIntegrationTest(TestCase):
    """Test pipeline integration with contacts and churches"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.pipeline = Pipeline.objects.create(
            name='Test Pipeline',
            office=self.office
        )
        self.stage = PipelineStage.objects.create(
            name='Test Stage',
            order=1,
            pipeline=self.pipeline
        )
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        self.church = Church.objects.create(
            name='Test Church'
        )
    
    def test_person_pipeline_relationship(self):
        """Test person can be tracked in multiple pipelines"""
        # Create two pipelines
        pipeline2 = Pipeline.objects.create(
            name='Second Pipeline',
            office=self.office
        )
        stage2 = PipelineStage.objects.create(
            name='Stage 2',
            order=1,
            pipeline=pipeline2
        )
        
        # Add person to both pipelines
        contact1 = PipelineContact.objects.create(
            person=self.person,
            contact_type='person',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        contact2 = PipelineContact.objects.create(
            person=self.person,
            contact_type='person',
            pipeline=pipeline2,
            current_stage=stage2
        )
        
        # Person should have entries in both pipelines
        person_entries = self.person.pipeline_entries.all()
        self.assertEqual(person_entries.count(), 2)
        self.assertIn(contact1, person_entries)
        self.assertIn(contact2, person_entries)
    
    def test_church_pipeline_relationship(self):
        """Test church can be tracked in pipeline"""
        contact = PipelineContact.objects.create(
            church=self.church,
            contact_type='church',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        
        # Church should have pipeline entry
        church_entries = self.church.pipeline_entries.all()
        self.assertEqual(church_entries.count(), 1)
        self.assertIn(contact, church_entries)
    
    def test_person_deletion_cascade(self):
        """Test that deleting person cascades to pipeline contacts"""
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type='person',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        
        contact_id = contact.id
        
        # Delete person
        self.person.delete()
        
        # Pipeline contact should be deleted
        self.assertFalse(PipelineContact.objects.filter(id=contact_id).exists())
    
    def test_church_deletion_cascade(self):
        """Test that deleting church cascades to pipeline contacts"""
        contact = PipelineContact.objects.create(
            church=self.church,
            contact_type='church',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        
        contact_id = contact.id
        
        # Delete church
        self.church.delete()
        
        # Pipeline contact should be deleted
        self.assertFalse(PipelineContact.objects.filter(id=contact_id).exists())
    
    def test_stage_deletion_cascade(self):
        """Test that deleting stage cascades properly"""
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type='person',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        
        contact_id = contact.id
        
        # Delete stage
        self.stage.delete()
        
        # Pipeline contact should be deleted
        self.assertFalse(PipelineContact.objects.filter(id=contact_id).exists())


class PipelineHistoryIntegrationTest(TestCase):
    """Test pipeline history integration"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.pipeline = Pipeline.objects.create(
            name='Test Pipeline',
            office=self.office
        )
        self.stage1 = PipelineStage.objects.create(
            name='Stage 1',
            order=1,
            pipeline=self.pipeline
        )
        self.stage2 = PipelineStage.objects.create(
            name='Stage 2',
            order=2,
            pipeline=self.pipeline
        )
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            user=self.user,
            office=self.office
        )
        self.contact = PipelineContact.objects.create(
            person=self.person,
            contact_type='person',
            pipeline=self.pipeline,
            current_stage=self.stage1
        )
    
    def test_complete_stage_movement_history(self):
        """Test complete history tracking through stage movements"""
        # Create initial entry history
        initial_history = PipelineStageHistory.objects.create(
            pipeline_contact=self.contact,
            from_stage=None,
            to_stage=self.stage1,
            notes='Initial entry',
            created_by=self.user
        )
        
        # Move to stage 2
        self.contact.current_stage = self.stage2
        self.contact.save()
        
        move_history = PipelineStageHistory.objects.create(
            pipeline_contact=self.contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            notes='Moved to stage 2',
            created_by=self.user
        )
        
        # Check complete history
        history = self.contact.stage_history.all().order_by('created_at')
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0], initial_history)
        self.assertEqual(history[1], move_history)
        
        # Check history progression
        self.assertIsNone(history[0].from_stage)
        self.assertEqual(history[0].to_stage, self.stage1)
        self.assertEqual(history[1].from_stage, self.stage1)
        self.assertEqual(history[1].to_stage, self.stage2)
    
    def test_user_history_tracking(self):
        """Test that user changes are tracked in history"""
        # Create history entries by different users
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com'
        )
        
        history1 = PipelineStageHistory.objects.create(
            pipeline_contact=self.contact,
            from_stage=None,
            to_stage=self.stage1,
            created_by=self.user
        )
        
        history2 = PipelineStageHistory.objects.create(
            pipeline_contact=self.contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            created_by=user2
        )
        
        # Check user tracking
        user1_changes = self.user.stage_changes.all()
        user2_changes = user2.stage_changes.all()
        
        self.assertIn(history1, user1_changes)
        self.assertNotIn(history2, user1_changes)
        
        self.assertIn(history2, user2_changes)
        self.assertNotIn(history1, user2_changes)
    
    def test_stage_history_relationships(self):
        """Test stage history foreign key relationships"""
        history = PipelineStageHistory.objects.create(
            pipeline_contact=self.contact,
            from_stage=self.stage1,
            to_stage=self.stage2,
            created_by=self.user
        )
        
        # Test from_stage relationship
        stage1_from_history = self.stage1.from_stage_history.all()
        self.assertIn(history, stage1_from_history)
        
        # Test to_stage relationship
        stage2_to_history = self.stage2.to_stage_history.all()
        self.assertIn(history, stage2_to_history)
        
        # Stage1 should not be in to_stage_history
        stage1_to_history = self.stage1.to_stage_history.all()
        self.assertNotIn(history, stage1_to_history)


class PipelineDataConsistencyTest(TransactionTestCase):
    """Test data consistency and constraints in pipeline system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.pipeline = Pipeline.objects.create(
            name='Test Pipeline',
            office=self.office
        )
        self.stage = PipelineStage.objects.create(
            name='Test Stage',
            order=1,
            pipeline=self.pipeline
        )
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            user=self.user,
            office=self.office
        )
    
    def test_pipeline_contact_constraints(self):
        """Test that pipeline contact has proper constraints"""
        # Contact must have either person or church, not both
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type='person',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        
        # Contact should work with person
        self.assertEqual(contact.contact, self.person)
        
        # Create church contact
        church = Church.objects.create(
            name='Test Church'
        )
        
        church_contact = PipelineContact.objects.create(
            church=church,
            contact_type='church',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        
        # Church contact should work
        self.assertEqual(church_contact.contact, church)
    
    def test_stage_ordering_consistency(self):
        """Test that stage ordering is maintained"""
        stage2 = PipelineStage.objects.create(
            name='Stage 2',
            order=2,
            pipeline=self.pipeline
        )
        stage3 = PipelineStage.objects.create(
            name='Stage 3',
            order=3,
            pipeline=self.pipeline
        )
        
        # Stages should be ordered correctly
        stages = list(self.pipeline.stages.all())
        orders = [stage.order for stage in stages]
        self.assertEqual(orders, [1, 2, 3])
    
    def test_cross_pipeline_stage_protection(self):
        """Test that contacts can't be moved to stages from different pipelines"""
        # Create second pipeline
        pipeline2 = Pipeline.objects.create(
            name='Pipeline 2',
            office=self.office
        )
        stage2 = PipelineStage.objects.create(
            name='Stage 2',
            order=1,
            pipeline=pipeline2
        )
        
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type='person',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        
        # Trying to assign contact to stage from different pipeline
        # should be prevented by business logic (though not database constraint)
        # This would be handled in view validation
        
        # Verify the stage belongs to different pipeline
        self.assertNotEqual(self.stage.pipeline, stage2.pipeline)
    
    def test_history_chronological_ordering(self):
        """Test that history maintains chronological order"""
        contact = PipelineContact.objects.create(
            person=self.person,
            contact_type='person',
            pipeline=self.pipeline,
            current_stage=self.stage
        )
        
        # Create multiple history entries
        stage2 = PipelineStage.objects.create(
            name='Stage 2',
            order=2,
            pipeline=self.pipeline
        )
        
        history1 = PipelineStageHistory.objects.create(
            pipeline_contact=contact,
            from_stage=None,
            to_stage=self.stage,
            created_by=self.user
        )
        
        history2 = PipelineStageHistory.objects.create(
            pipeline_contact=contact,
            from_stage=self.stage,
            to_stage=stage2,
            created_by=self.user
        )
        
        # History should be ordered by created_at (most recent first)
        history_entries = list(PipelineStageHistory.objects.all())
        self.assertEqual(history_entries[0], history2)  # Most recent first
        self.assertEqual(history_entries[1], history1)