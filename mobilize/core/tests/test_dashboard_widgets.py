"""
Tests for dashboard widgets functionality
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from mobilize.core.models import DashboardPreference
from mobilize.core.dashboard_widgets import (
    get_user_dashboard_config,
    organize_widgets_by_row,
    get_widget_css_class,
    update_widget_preferences,
    toggle_widget,
    reorder_widgets,
    DEFAULT_WIDGETS,
)
from mobilize.contacts.models import Person
from mobilize.churches.models import Church

User = get_user_model()


class DashboardWidgetsTests(TestCase):
    """Test cases for dashboard widget functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", role="standard_user"
        )

    def test_default_widgets_structure(self):
        """Test that DEFAULT_WIDGETS has proper structure"""
        self.assertIsInstance(DEFAULT_WIDGETS, list)
        self.assertGreater(len(DEFAULT_WIDGETS), 0)

        for widget in DEFAULT_WIDGETS:
            self.assertIn("id", widget)
            self.assertIn("name", widget)
            self.assertIn("description", widget)
            self.assertIn("enabled", widget)
            self.assertIn("order", widget)
            self.assertIn("size", widget)

    def test_get_user_dashboard_config_creates_new(self):
        """Test that get_user_dashboard_config creates new preferences"""
        self.assertFalse(DashboardPreference.objects.filter(user=self.user).exists())

        prefs = get_user_dashboard_config(self.user)

        self.assertIsInstance(prefs, DashboardPreference)
        self.assertEqual(prefs.user, self.user)
        self.assertTrue(DashboardPreference.objects.filter(user=self.user).exists())

    def test_get_user_dashboard_config_returns_existing(self):
        """Test that get_user_dashboard_config returns existing preferences"""
        # Create existing preferences
        existing_prefs = DashboardPreference.objects.create(
            user=self.user, widget_config={"widgets": [{"id": "test", "name": "Test"}]}
        )

        prefs = get_user_dashboard_config(self.user)

        self.assertEqual(prefs.id, existing_prefs.id)
        self.assertEqual(prefs.widget_config["widgets"][0]["id"], "test")

    def test_dashboard_preference_get_widget_config(self):
        """Test DashboardPreference.get_widget_config method"""
        prefs = DashboardPreference.objects.create(user=self.user)

        # Should return default widgets when config is empty
        widgets = prefs.get_widget_config()
        self.assertEqual(widgets, DEFAULT_WIDGETS)

        # Should return custom config when set
        custom_widgets = [{"id": "custom", "name": "Custom Widget"}]
        prefs.widget_config = {"widgets": custom_widgets}
        prefs.save()

        widgets = prefs.get_widget_config()
        self.assertEqual(widgets, custom_widgets)

    def test_dashboard_preference_get_enabled_widgets(self):
        """Test DashboardPreference.get_enabled_widgets method"""
        prefs = DashboardPreference.objects.create(user=self.user)

        # Set custom widgets with some disabled
        custom_widgets = [
            {"id": "widget1", "name": "Widget 1", "enabled": True, "order": 2},
            {"id": "widget2", "name": "Widget 2", "enabled": False, "order": 1},
            {"id": "widget3", "name": "Widget 3", "enabled": True, "order": 3},
        ]
        prefs.set_widget_config(custom_widgets)

        enabled_widgets = prefs.get_enabled_widgets()

        # Should only return enabled widgets, sorted by order
        self.assertEqual(len(enabled_widgets), 2)
        self.assertEqual(enabled_widgets[0]["id"], "widget1")
        self.assertEqual(enabled_widgets[1]["id"], "widget3")

    def test_dashboard_preference_reset_to_defaults(self):
        """Test DashboardPreference.reset_to_defaults method"""
        prefs = DashboardPreference.objects.create(
            user=self.user, widget_config={"widgets": [{"id": "custom"}]}
        )

        prefs.reset_to_defaults()

        widgets = prefs.get_widget_config()
        self.assertEqual(widgets, DEFAULT_WIDGETS)

    def test_organize_widgets_by_row(self):
        """Test organize_widgets_by_row function"""
        widgets = [
            {"id": "w1", "size": "full"},
            {"id": "w2", "size": "half"},
            {"id": "w3", "size": "half"},
            {"id": "w4", "size": "one_third"},
            {"id": "w5", "size": "two_thirds"},
        ]

        rows = organize_widgets_by_row(widgets)

        # First row: full widget
        self.assertEqual(len(rows[0]), 1)
        self.assertEqual(rows[0][0]["id"], "w1")

        # Second row: two half widgets
        self.assertEqual(len(rows[1]), 2)
        self.assertEqual(rows[1][0]["id"], "w2")
        self.assertEqual(rows[1][1]["id"], "w3")

        # Third row: one_third + two_thirds
        self.assertEqual(len(rows[2]), 2)
        self.assertEqual(rows[2][0]["id"], "w4")
        self.assertEqual(rows[2][1]["id"], "w5")

    def test_get_widget_css_class(self):
        """Test get_widget_css_class function"""
        self.assertEqual(get_widget_css_class("full"), "col-12")
        self.assertEqual(get_widget_css_class("two_thirds"), "col-lg-8")
        self.assertEqual(get_widget_css_class("half"), "col-lg-6")
        self.assertEqual(get_widget_css_class("one_third"), "col-lg-4")
        self.assertEqual(get_widget_css_class("quarter"), "col-lg-3")
        self.assertEqual(get_widget_css_class("unknown"), "col-12")

    def test_update_widget_preferences(self):
        """Test update_widget_preferences function"""
        prefs = get_user_dashboard_config(self.user)

        # Update some widget properties
        widget_updates = {
            "metrics_summary": {"enabled": False},
            "weekly_summary": {"size": "full", "order": 1},
        }

        updated_prefs = update_widget_preferences(self.user, widget_updates)

        widgets = updated_prefs.get_widget_config()

        # Find updated widgets
        metrics_widget = next(w for w in widgets if w["id"] == "metrics_summary")
        weekly_widget = next(w for w in widgets if w["id"] == "weekly_summary")

        self.assertFalse(metrics_widget["enabled"])
        self.assertEqual(weekly_widget["size"], "full")
        self.assertEqual(weekly_widget["order"], 1)

    def test_toggle_widget(self):
        """Test toggle_widget function"""
        prefs = get_user_dashboard_config(self.user)

        # Toggle a widget off
        updated_prefs = toggle_widget(self.user, "metrics_summary", False)

        widgets = updated_prefs.get_widget_config()
        metrics_widget = next(w for w in widgets if w["id"] == "metrics_summary")

        self.assertFalse(metrics_widget["enabled"])

        # Toggle it back on
        updated_prefs = toggle_widget(self.user, "metrics_summary", True)

        widgets = updated_prefs.get_widget_config()
        metrics_widget = next(w for w in widgets if w["id"] == "metrics_summary")

        self.assertTrue(metrics_widget["enabled"])

    def test_reorder_widgets(self):
        """Test reorder_widgets function"""
        prefs = get_user_dashboard_config(self.user)

        # Get original widget IDs
        original_widgets = prefs.get_widget_config()
        widget_ids = [w["id"] for w in original_widgets]

        # Reverse the order
        new_order = list(reversed(widget_ids))

        updated_prefs = reorder_widgets(self.user, new_order)

        reordered_widgets = updated_prefs.get_widget_config()

        # Check that order was updated correctly
        for i, widget in enumerate(reordered_widgets):
            self.assertEqual(widget["order"], i + 1)
            if i < len(new_order):
                self.assertEqual(widget["id"], new_order[i])

    def test_dashboard_preference_model_methods(self):
        """Test DashboardPreference model methods"""
        prefs = DashboardPreference.objects.create(user=self.user)

        # Test string representation
        self.assertIn(self.user.username, str(prefs))

        # Test that timestamps are set
        self.assertIsNotNone(prefs.created_at)
        self.assertIsNotNone(prefs.updated_at)
