"""
Basic test to verify the test setup works.
"""

from django.test import TestCase


class BasicTestCase(TestCase):
    """Basic test case to verify the test setup works."""

    def test_basic(self):
        """Test that True is True."""
        self.assertTrue(True)
