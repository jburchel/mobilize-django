"""
Tests for the sync_supabase management command.
"""

from io import StringIO
from unittest.mock import patch, MagicMock

from django.core.management import call_command
from django.test import TestCase


class SyncSupabaseCommandTest(TestCase):
    """Test the sync_supabase management command."""

    def setUp(self):
        """Set up test environment."""
        self.out = StringIO()
        self.err = StringIO()

        # Set up patches for Supabase client
        patcher = patch("mobilize.utils.supabase_client.supabase")
        self.mock_supabase = patcher.start()
        self.addCleanup(patcher.stop)

    @patch("mobilize.contacts.models.Contact.objects.first")
    @patch("mobilize.contacts.models.Contact.objects.all")
    @patch("mobilize.utils.supabase_sync.SupabaseSync.sync_to_supabase")
    def test_sync_contact_to_supabase(self, mock_sync, mock_all, mock_first):
        """Test syncing Contact model to Supabase."""
        # Mock the Contact.objects.first() call to avoid database errors
        mock_first.return_value = None

        # Mock the Contact.objects.all() queryset
        mock_contact = MagicMock()
        mock_contact.id = 1
        mock_queryset = MagicMock()
        mock_queryset.count.return_value = 1
        mock_queryset.__iter__.return_value = [mock_contact]
        mock_all.return_value = mock_queryset

        # Mock the SupabaseSync.sync_to_supabase method
        mock_sync.return_value = {"id": 1, "name": "Test Contact"}

        # Call the command
        call_command(
            "sync_supabase",
            direction="to_supabase",
            model="contact",
            stdout=self.out,
            stderr=self.err,
        )

        # Check that the command output contains expected text
        output = self.out.getvalue()
        self.assertIn("Starting synchronization with parameters:", output)
        self.assertIn("Direction: to_supabase", output)
        self.assertIn("Models: Contact", output)
        self.assertIn("Found 1 Contact instances to sync", output)
        self.assertIn("Synced Contact #1", output)
        self.assertIn("Synchronization completed successfully", output)

        # Check that the sync method was called with the mock contact
        mock_sync.assert_called_once_with(mock_contact)

        # Check that the summary was printed
        self.assertIn("Sync summary for Contact:", output)
        self.assertIn("Success:", output)

    @patch("mobilize.contacts.models.Contact.objects.first")
    def test_sync_with_missing_table(self, mock_first):
        """Test syncing when the table doesn't exist."""
        # Simulate the table not existing
        mock_first.side_effect = Exception('relation "contacts" does not exist')

        # Call the command
        call_command(
            "sync_supabase",
            direction="to_supabase",
            model="contact",
            stdout=self.out,
            stderr=self.err,
        )

        # Check that the command output contains the warning about missing table
        output = self.out.getvalue()
        self.assertIn("Table for Contact does not exist in the database", output)
        self.assertIn("Run migrations first", output)

    def test_dry_run(self):
        """Test dry run mode."""
        with patch(
            "mobilize.utils.management.commands.sync_supabase.Command._sync_to_supabase"
        ), patch(
            "mobilize.utils.management.commands.sync_supabase.Command._sync_from_supabase"
        ):
            # Call the command with dry run
            call_command(
                "sync_supabase",
                direction="both",
                model="all",
                dry_run=True,
                stdout=self.out,
                stderr=self.err,
            )

            # Check that the command output indicates dry run
            output = self.out.getvalue()
            self.assertIn("Dry run: Yes", output)

    def test_sync_from_supabase(self):
        """Test syncing from Supabase to Django."""
        # Mock the _sync_from_supabase method directly
        with patch(
            "mobilize.utils.management.commands.sync_supabase.Command._sync_from_supabase"
        ) as mock_sync_method:
            # Call the command
            call_command(
                "sync_supabase",
                direction="from_supabase",
                model="contact",
                stdout=self.out,
                stderr=self.err,
            )

            # Check that the command output contains expected text
            output = self.out.getvalue()
            self.assertIn("Direction: from_supabase", output)
            self.assertIn("Models: Contact", output)

            # Verify the method was called with the right parameters
            mock_sync_method.assert_called_once()

    def test_sync_from_supabase_no_records(self):
        """Test syncing from Supabase when no records are found."""
        # Mock the fetch_all method to return empty list
        self.mock_supabase.fetch_all.return_value = []

        with patch("mobilize.contacts.models.Contact.objects.first") as mock_first:
            mock_first.return_value = None

            # Call the command
            call_command(
                "sync_supabase",
                direction="from_supabase",
                model="contact",
                stdout=self.out,
                stderr=self.err,
            )

            # Check that the command output contains expected text
            output = self.out.getvalue()
            self.assertIn("Synchronizing Contact...", output)
