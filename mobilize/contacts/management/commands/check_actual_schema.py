"""
Management command to check the actual database schema vs Django models.
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Check actual database schema for contacts and people tables"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Checking Actual Database Schema ==="))

        cursor = connection.cursor()

        # Check all columns in contacts table
        self.stdout.write("\\n=== CONTACTS TABLE SCHEMA ===")
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'contacts' 
            ORDER BY ordinal_position;
        """
        )

        contacts_columns = cursor.fetchall()
        for col in contacts_columns:
            self.stdout.write(
                f'{col[0]:25} | {col[1]:15} | Null: {col[2]:5} | Default: {col[3] or "None"}'
            )

        # Check all columns in people table
        self.stdout.write("\\n=== PEOPLE TABLE SCHEMA ===")
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'people' 
            ORDER BY ordinal_position;
        """
        )

        people_columns = cursor.fetchall()
        for col in people_columns:
            self.stdout.write(
                f'{col[0]:25} | {col[1]:15} | Null: {col[2]:5} | Default: {col[3] or "None"}'
            )

        # Check for any tables that might contain name data
        self.stdout.write("\\n=== ALL TABLES IN DATABASE ===")
        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        )

        all_tables = cursor.fetchall()
        for table in all_tables:
            self.stdout.write(f"{table[0]}")

        # Look for any columns with 'name' in them across all tables
        self.stdout.write('\\n=== COLUMNS CONTAINING "name" ===')
        cursor.execute(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns 
            WHERE column_name ILIKE '%name%'
            AND table_schema = 'public'
            ORDER BY table_name, column_name;
        """
        )

        name_columns = cursor.fetchall()
        for col in name_columns:
            self.stdout.write(f"{col[0]:20} | {col[1]:25} | {col[2]}")

        # Check a few specific people records that should have names
        self.stdout.write("\\n=== SAMPLE DATA FROM PEOPLE TABLE ===")
        cursor.execute(
            """
            SELECT contact_id, title, preferred_name 
            FROM people 
            WHERE contact_id IN (699, 728, 685)
            ORDER BY contact_id;
        """
        )

        sample_people = cursor.fetchall()
        if sample_people:
            self.stdout.write("Person samples (contact_id, title, preferred_name):")
            for person in sample_people:
                self.stdout.write(
                    f'  {person[0]} | {person[1] or "NULL"} | {person[2] or "NULL"}'
                )
        else:
            self.stdout.write("No sample people found with those IDs")

        # Check sample data from contacts table
        self.stdout.write("\\n=== SAMPLE DATA FROM CONTACTS TABLE ===")
        cursor.execute(
            """
            SELECT id, first_name, last_name, email, type
            FROM contacts 
            WHERE id IN (699, 728, 685)
            ORDER BY id;
        """
        )

        sample_contacts = cursor.fetchall()
        if sample_contacts:
            self.stdout.write(
                "Contact samples (id, first_name, last_name, email, type):"
            )
            for contact in sample_contacts:
                self.stdout.write(
                    f'  {contact[0]} | {contact[1] or "NULL"} | {contact[2] or "NULL"} | {contact[3] or "NULL"} | {contact[4]}'
                )
        else:
            self.stdout.write("No sample contacts found with those IDs")

        self.stdout.write("\\n" + self.style.SUCCESS("Schema check complete!"))
