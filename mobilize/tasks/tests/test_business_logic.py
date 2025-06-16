"""
Business logic tests for Task app - testing complex workflows and automation.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from unittest.mock import patch, MagicMock
import json

from mobilize.admin_panel.models import Office, UserOffice
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.tasks.models import Task

User = get_user_model()


class TaskRecurringBusinessLogicTest(TestCase):
    """Test business logic for recurring task functionality"""
    
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
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
    
    def test_daily_recurrence_calculation(self):
        """Test daily recurrence pattern calculation"""
        pattern = {'frequency': 'daily', 'interval': 2}
        
        template = Task.objects.create(
            title='Daily Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                date(2024, 1, 1), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        expected_date = date(2024, 1, 3)  # 2 days later
        
        self.assertIsNotNone(next_occurrence)
        self.assertEqual(next_occurrence.date(), expected_date)
    
    def test_weekly_recurrence_with_weekdays(self):
        """Test weekly recurrence with specific weekdays"""
        pattern = {
            'frequency': 'weekly',
            'interval': 1,
            'weekdays': [0, 2, 4]  # Monday, Wednesday, Friday
        }
        
        # Start on a Sunday (weekday 6)
        sunday = date(2024, 1, 7)  # January 7, 2024 is a Sunday
        
        template = Task.objects.create(
            title='Weekly Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                sunday, datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        
        # Should be Monday (next valid weekday)
        self.assertIsNotNone(next_occurrence)
        self.assertEqual(next_occurrence.weekday(), 0)  # Monday
        self.assertEqual(next_occurrence.date(), date(2024, 1, 8))
    
    def test_weekly_recurrence_without_weekdays(self):
        """Test weekly recurrence without specific weekdays"""
        pattern = {'frequency': 'weekly', 'interval': 2}
        
        template = Task.objects.create(
            title='Weekly Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                date(2024, 1, 1), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        expected_date = date(2024, 1, 15)  # 2 weeks later
        
        self.assertIsNotNone(next_occurrence)
        self.assertEqual(next_occurrence.date(), expected_date)
    
    def test_monthly_recurrence_with_day_of_month(self):
        """Test monthly recurrence with specific day of month"""
        pattern = {
            'frequency': 'monthly',
            'interval': 1,
            'day_of_month': 15
        }
        
        template = Task.objects.create(
            title='Monthly Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                date(2024, 1, 1), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        expected_date = date(2024, 2, 15)  # 15th of next month
        
        self.assertIsNotNone(next_occurrence)
        self.assertEqual(next_occurrence.date(), expected_date)
    
    def test_monthly_recurrence_without_day_of_month(self):
        """Test monthly recurrence without specific day"""
        pattern = {'frequency': 'monthly', 'interval': 2}
        
        template = Task.objects.create(
            title='Monthly Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                date(2024, 1, 15), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        expected_date = date(2024, 3, 15)  # 2 months later
        
        self.assertIsNotNone(next_occurrence)
        self.assertEqual(next_occurrence.date(), expected_date)
    
    def test_recurrence_end_date_respect(self):
        """Test that recurrence respects end date"""
        pattern = {'frequency': 'daily', 'interval': 1}
        end_date = date(2024, 1, 5)
        
        template = Task.objects.create(
            title='Ending Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            recurrence_end_date=end_date,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                date(2024, 1, 10), datetime.min.time()  # After end date
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        self.assertIsNone(next_occurrence)  # Should be None due to end date
    
    def test_invalid_frequency_returns_none(self):
        """Test that invalid frequency returns None"""
        pattern = {'frequency': 'invalid', 'interval': 1}
        
        template = Task.objects.create(
            title='Invalid Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                date(2024, 1, 1), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        self.assertIsNone(next_occurrence)
    
    def test_generate_occurrence_copies_all_fields(self):
        """Test that generating occurrence copies all relevant fields"""
        pattern = {'frequency': 'daily', 'interval': 1}
        
        template = Task.objects.create(
            title='Template Task',
            description='Template description',
            priority='high',
            category='meetings',
            type='recurring',
            recurring_pattern=pattern,
            is_recurring_template=True,
            person=self.person,
            created_by=self.user,
            assigned_to=self.user,
            office=self.office,
            due_time='14:00',
            due_time_details='Afternoon meeting',
            reminder_time='13:30',
            reminder_option='30_minutes',
            google_calendar_sync_enabled=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                date(2024, 1, 1), datetime.min.time()
            ))
        )
        
        occurrence = template.generate_next_occurrence()
        
        self.assertIsNotNone(occurrence)
        
        # Check copied fields
        self.assertEqual(occurrence.title, template.title)
        self.assertEqual(occurrence.description, template.description)
        self.assertEqual(occurrence.priority, template.priority)
        self.assertEqual(occurrence.category, template.category)
        self.assertEqual(occurrence.type, template.type)
        self.assertEqual(occurrence.person, template.person)
        self.assertEqual(occurrence.created_by, template.created_by)
        self.assertEqual(occurrence.assigned_to, template.assigned_to)
        self.assertEqual(occurrence.office, template.office)
        self.assertEqual(occurrence.due_time, template.due_time)
        self.assertEqual(occurrence.due_time_details, template.due_time_details)
        self.assertEqual(occurrence.reminder_time, template.reminder_time)
        self.assertEqual(occurrence.reminder_option, template.reminder_option)
        self.assertEqual(occurrence.google_calendar_sync_enabled, template.google_calendar_sync_enabled)
        
        # Check occurrence-specific fields
        self.assertEqual(occurrence.parent_task, template)
        self.assertFalse(occurrence.is_recurring_template)
        self.assertEqual(occurrence.status, 'pending')
        self.assertIsNone(occurrence.recurring_pattern)
        self.assertIsNotNone(occurrence.due_date)
    
    def test_generate_pending_occurrences_multiple_templates(self):
        """Test generating occurrences for multiple templates"""
        pattern = {'frequency': 'daily', 'interval': 1}
        
        # Create multiple templates
        template1 = Task.objects.create(
            title='Daily Task 1',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.now() + timedelta(days=1),
            recurrence_end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user,
            office=self.office
        )
        
        template2 = Task.objects.create(
            title='Daily Task 2',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.now() + timedelta(days=2),
            recurrence_end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user,
            office=self.office
        )
        
        # Generate occurrences for next 7 days
        generated_count = Task.generate_pending_occurrences(days_ahead=7)
        
        # Should generate occurrences
        self.assertGreater(generated_count, 0)
        
        # Check that occurrences were created for both templates
        occurrences1 = Task.objects.filter(parent_task=template1)
        occurrences2 = Task.objects.filter(parent_task=template2)
        
        self.assertGreater(occurrences1.count(), 0)
        self.assertGreater(occurrences2.count(), 0)
    
    def test_generate_pending_occurrences_respects_end_date(self):
        """Test that batch generation respects end dates"""
        pattern = {'frequency': 'daily', 'interval': 1}
        
        # Template that ends soon
        template = Task.objects.create(
            title='Ending Soon Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.now() + timedelta(days=1),
            recurrence_end_date=timezone.now().date() + timedelta(days=2),
            created_by=self.user,
            office=self.office
        )
        
        # Generate occurrences for next 30 days
        generated_count = Task.generate_pending_occurrences(days_ahead=30)
        
        # Should only generate limited occurrences due to end date
        occurrences = Task.objects.filter(parent_task=template)
        self.assertLessEqual(occurrences.count(), 3)  # At most 2-3 occurrences


class TaskCompletionBusinessLogicTest(TestCase):
    """Test business logic for task completion"""
    
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
    
    def test_is_completed_property_logic(self):
        """Test is_completed property business logic"""
        # Pending task
        pending_task = Task.objects.create(
            title='Pending Task',
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(pending_task.is_completed)
        
        # In progress task
        in_progress_task = Task.objects.create(
            title='In Progress Task',
            status='in_progress',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(in_progress_task.is_completed)
        
        # Completed by status
        completed_by_status = Task.objects.create(
            title='Completed by Status',
            status='completed',
            created_by=self.user,
            office=self.office
        )
        self.assertTrue(completed_by_status.is_completed)
        
        # Completed by completed_at field
        completed_by_date = Task.objects.create(
            title='Completed by Date',
            status='pending',
            completed_at=timezone.now(),
            created_by=self.user,
            office=self.office
        )
        self.assertTrue(completed_by_date.is_completed)
    
    def test_is_overdue_property_logic(self):
        """Test is_overdue property business logic"""
        now = timezone.now()
        
        # Future due date - not overdue
        future_task = Task.objects.create(
            title='Future Task',
            due_date=now.date() + timedelta(days=7),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(future_task.is_overdue)
        
        # Today's due date - not overdue
        today_task = Task.objects.create(
            title='Today Task',
            due_date=now.date(),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(today_task.is_overdue)
        
        # Past due date - overdue
        overdue_task = Task.objects.create(
            title='Overdue Task',
            due_date=now.date() - timedelta(days=1),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertTrue(overdue_task.is_overdue)
        
        # No due date - not overdue
        no_due_date_task = Task.objects.create(
            title='No Due Date Task',
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(no_due_date_task.is_overdue)
        
        # Completed task with past due date - not overdue
        completed_overdue_task = Task.objects.create(
            title='Completed Overdue Task',
            due_date=now.date() - timedelta(days=1),
            status='completed',
            completed_at=now,
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(completed_overdue_task.is_overdue)


class TaskPriorityBusinessLogicTest(TestCase):
    """Test business logic for task prioritization"""
    
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
    
    def test_priority_ordering_logic(self):
        """Test task priority ordering business logic"""
        # Create tasks with different priorities
        low_task = Task.objects.create(
            title='Low Priority Task',
            priority='low',
            created_by=self.user,
            office=self.office
        )
        
        medium_task = Task.objects.create(
            title='Medium Priority Task',
            priority='medium',
            created_by=self.user,
            office=self.office
        )
        
        high_task = Task.objects.create(
            title='High Priority Task',
            priority='high',
            created_by=self.user,
            office=self.office
        )
        
        # Test ordering by priority
        tasks_by_priority = Task.objects.order_by('priority')
        priority_order = [task.priority for task in tasks_by_priority]
        
        # Should be ordered alphabetically: high, low, medium
        expected_order = ['high', 'low', 'medium']
        self.assertEqual(priority_order, expected_order)
    
    def test_combined_due_date_priority_logic(self):
        """Test combined due date and priority ordering logic"""
        now = timezone.now()
        
        # High priority, far due date
        high_far = Task.objects.create(
            title='High Priority Far',
            priority='high',
            due_date=now.date() + timedelta(days=10),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        
        # Low priority, near due date
        low_near = Task.objects.create(
            title='Low Priority Near',
            priority='low',
            due_date=now.date() + timedelta(days=1),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        
        # High priority, near due date
        high_near = Task.objects.create(
            title='High Priority Near',
            priority='high',
            due_date=now.date() + timedelta(days=1),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        
        # Test business logic for urgency calculation
        # This would typically be used in views or managers
        def calculate_urgency_score(task):
            """Calculate urgency score for task prioritization"""
            priority_scores = {'low': 1, 'medium': 2, 'high': 3}
            priority_score = priority_scores.get(task.priority, 1)
            
            if task.due_date:
                days_until_due = (task.due_date - timezone.now().date()).days
                if days_until_due < 0:
                    urgency_score = 10  # Overdue
                elif days_until_due <= 1:
                    urgency_score = 5   # Due soon
                elif days_until_due <= 7:
                    urgency_score = 3   # Due this week
                else:
                    urgency_score = 1   # Due later
            else:
                urgency_score = 0  # No due date
            
            return priority_score * urgency_score
        
        # Calculate urgency scores
        high_far_score = calculate_urgency_score(high_far)
        low_near_score = calculate_urgency_score(low_near)
        high_near_score = calculate_urgency_score(high_near)
        
        # High priority + near due date should have highest score
        self.assertGreater(high_near_score, high_far_score)
        self.assertGreater(high_near_score, low_near_score)


class TaskReminderBusinessLogicTest(TestCase):
    """Test business logic for task reminders"""
    
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
    
    def test_reminder_logic(self):
        """Test task reminder business logic"""
        now = timezone.now()
        
        # Task with reminder set for future (due in 2 days, reminder 1 day before)
        future_reminder_task = Task.objects.create(
            title='Future Reminder Task',
            due_date=now.date() + timedelta(days=2),
            reminder_option='1_day',
            reminder_sent=False,
            created_by=self.user,
            office=self.office
        )
        
        # Task with reminder already sent
        sent_reminder_task = Task.objects.create(
            title='Sent Reminder Task',
            due_date=now.date() + timedelta(days=1),
            reminder_option='1_day',
            reminder_sent=True,
            created_by=self.user,
            office=self.office
        )
        
        # Task with no reminder
        no_reminder_task = Task.objects.create(
            title='No Reminder Task',
            due_date=now.date() + timedelta(days=1),
            reminder_option='none',
            reminder_sent=False,
            created_by=self.user,
            office=self.office
        )
        
        def should_send_reminder(task):
            """Business logic for determining if reminder should be sent"""
            if task.reminder_sent or task.reminder_option == 'none':
                return False
            
            if not task.due_date:
                return False
            
            reminder_mapping = {
                '15_minutes': timedelta(minutes=15),
                '30_minutes': timedelta(minutes=30),
                '1_hour': timedelta(hours=1),
                '1_day': timedelta(days=1),
                '1_week': timedelta(weeks=1)
            }
            
            reminder_delta = reminder_mapping.get(task.reminder_option)
            if not reminder_delta:
                return False
            
            reminder_time = timezone.make_aware(
                datetime.combine(task.due_date, datetime.min.time())
            ) - reminder_delta
            
            return timezone.now() >= reminder_time
        
        # Test reminder logic
        self.assertFalse(should_send_reminder(future_reminder_task))  # Too early
        self.assertFalse(should_send_reminder(sent_reminder_task))    # Already sent
        self.assertFalse(should_send_reminder(no_reminder_task))      # No reminder set
    
    def test_overdue_task_logic(self):
        """Test business logic for overdue task handling"""
        now = timezone.now()
        
        # Overdue task
        overdue_task = Task.objects.create(
            title='Overdue Task',
            due_date=now.date() - timedelta(days=2),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        
        # Very overdue task
        very_overdue_task = Task.objects.create(
            title='Very Overdue Task',
            due_date=now.date() - timedelta(days=30),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        
        def get_overdue_severity(task):
            """Business logic for determining overdue severity"""
            if not task.due_date or task.is_completed:
                return 'none'
            
            days_overdue = (timezone.now().date() - task.due_date).days
            
            if days_overdue <= 0:
                return 'none'
            elif days_overdue <= 7:
                return 'mild'
            elif days_overdue <= 30:
                return 'moderate'
            else:
                return 'severe'
        
        # Test overdue severity
        self.assertEqual(get_overdue_severity(overdue_task), 'mild')
        self.assertEqual(get_overdue_severity(very_overdue_task), 'moderate')


class TaskAutomationBusinessLogicTest(TestCase):
    """Test business logic for task automation features"""
    
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
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
    
    def test_task_category_logic(self):
        """Test task categorization business logic"""
        # Create tasks with different categories
        meeting_task = Task.objects.create(
            title='Team Meeting',
            category='meetings',
            type='meeting',
            created_by=self.user,
            office=self.office
        )
        
        follow_up_task = Task.objects.create(
            title='Follow up with client',
            category='follow_ups',
            type='communication',
            person=self.person,
            created_by=self.user,
            office=self.office
        )
        
        def get_task_type_recommendations(task):
            """Business logic for task type recommendations"""
            recommendations = []
            
            if task.person:
                recommendations.append('person_related')
            
            if task.category == 'meetings':
                recommendations.append('schedule_reminder')
                recommendations.append('prepare_agenda')
            
            if task.category == 'follow_ups':
                recommendations.append('set_reminder')
                recommendations.append('track_response')
            
            if 'meeting' in task.title.lower():
                recommendations.append('meeting_prep')
            
            return recommendations
        
        # Test recommendations
        meeting_recommendations = get_task_type_recommendations(meeting_task)
        follow_up_recommendations = get_task_type_recommendations(follow_up_task)
        
        self.assertIn('schedule_reminder', meeting_recommendations)
        self.assertIn('meeting_prep', meeting_recommendations)
        
        self.assertIn('person_related', follow_up_recommendations)
        self.assertIn('set_reminder', follow_up_recommendations)
        self.assertIn('track_response', follow_up_recommendations)
    
    def test_task_assignment_logic(self):
        """Test task assignment business logic"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com'
        )
        
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com'
        )
        
        # Create user office relationships
        UserOffice.objects.create(
            user=admin_user,
            office=self.office,
            role='office_admin'
        )
        
        UserOffice.objects.create(
            user=regular_user,
            office=self.office,
            role='standard_user'
        )
        
        def get_assignment_suggestions(task, requester):
            """Business logic for task assignment suggestions"""
            suggestions = []
            
            # Self-assignment
            suggestions.append({
                'user': requester,
                'reason': 'self_assignment',
                'priority': 1
            })
            
            # Same office users
            office_users = User.objects.filter(
                useroffice__office=task.office
            ).exclude(id=requester.id)
            
            for user in office_users:
                user_office = user.useroffice_set.filter(office=task.office).first()
                if user_office:
                    priority = 2 if user_office.role == 'office_admin' else 3
                    suggestions.append({
                        'user': user,
                        'reason': f'office_member_{user_office.role}',
                        'priority': priority
                    })
            
            # Sort by priority
            return sorted(suggestions, key=lambda x: x['priority'])
        
        # Test assignment suggestions
        task = Task.objects.create(
            title='Assignment Test Task',
            office=self.office,
            created_by=self.user
        )
        
        suggestions = get_assignment_suggestions(task, self.user)
        
        # Should suggest self first, then office admin, then regular user
        self.assertEqual(suggestions[0]['user'], self.user)
        self.assertEqual(suggestions[0]['reason'], 'self_assignment')
        
        # Find admin suggestion
        admin_suggestion = next(
            (s for s in suggestions if s['user'] == admin_user), None
        )
        self.assertIsNotNone(admin_suggestion)
        self.assertEqual(admin_suggestion['reason'], 'office_member_office_admin')
    
    def test_task_deadline_calculation(self):
        """Test business logic for calculating task deadlines"""
        def calculate_suggested_deadline(task_type, urgency='medium'):
            """Business logic for suggesting task deadlines"""
            urgency_multipliers = {
                'low': 2.0,
                'medium': 1.0,
                'high': 0.5
            }
            
            base_deadlines = {
                'follow_up': timedelta(days=3),
                'meeting': timedelta(days=7),
                'research': timedelta(days=14),
                'general': timedelta(days=7)
            }
            
            base_deadline = base_deadlines.get(task_type, timedelta(days=7))
            multiplier = urgency_multipliers.get(urgency, 1.0)
            
            suggested_deadline = timezone.now() + (base_deadline * multiplier)
            return suggested_deadline.date()
        
        # Test deadline calculations
        follow_up_high = calculate_suggested_deadline('follow_up', 'high')
        follow_up_low = calculate_suggested_deadline('follow_up', 'low')
        
        meeting_medium = calculate_suggested_deadline('meeting', 'medium')
        research_medium = calculate_suggested_deadline('research', 'medium')
        
        # High urgency should have shorter deadline
        self.assertLess(follow_up_high, follow_up_low)
        
        # Research tasks should have longer deadlines than meetings
        self.assertGreater(research_medium, meeting_medium)
    
    @patch('mobilize.tasks.models.timezone.now')
    def test_bulk_occurrence_generation(self, mock_now):
        """Test bulk generation of recurring task occurrences"""
        # Mock current time for predictable testing
        mock_now.return_value = timezone.make_aware(datetime(2024, 1, 1, 12, 0, 0))
        
        pattern = {'frequency': 'daily', 'interval': 1}
        
        # Create multiple templates
        templates = []
        for i in range(5):
            template = Task.objects.create(
                title=f'Daily Template {i}',
                recurring_pattern=pattern,
                is_recurring_template=True,
                next_occurrence_date=timezone.make_aware(datetime(2024, 1, 2, 9, 0, 0)),
                recurrence_end_date=date(2024, 1, 31),
                created_by=self.user,
                office=self.office
            )
            templates.append(template)
        
        # Generate occurrences
        generated_count = Task.generate_pending_occurrences(days_ahead=7)
        
        # Should generate multiple occurrences for each template
        self.assertGreater(generated_count, 0)
        
        # Verify each template has occurrences
        for template in templates:
            occurrences = Task.objects.filter(parent_task=template)
            self.assertGreater(occurrences.count(), 0)
            
            # All occurrences should be within the next 7 days
            cutoff_date = timezone.now() + timedelta(days=8)  # Buffer for edge cases
            for occurrence in occurrences:
                occurrence_datetime = timezone.make_aware(
                    datetime.combine(occurrence.due_date, datetime.min.time())
                )
                self.assertLessEqual(occurrence_datetime, cutoff_date)