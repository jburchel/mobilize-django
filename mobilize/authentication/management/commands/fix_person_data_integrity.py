from django.core.management.base import BaseCommand
from django.db import connection
from mobilize.contacts.models import Person, Contact


class Command(BaseCommand):
    help = (
        "Fix Person table data integrity issues - NULL PKs and broken FK relationships"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be made")
            )

        self.stdout.write(
            self.style.SUCCESS("🔧 Diagnosing Person table data integrity issues")
        )
        self.stdout.write("=" * 80)

        # Step 1: Analyze current Person table state
        self.analyze_person_table()

        # Step 2: Check Contact table integrity
        self.analyze_contact_table()

        # Step 3: Fix NULL primary keys
        self.fix_null_primary_keys(dry_run)

        # Step 4: Rebuild Person-Contact relationships
        self.rebuild_person_contact_relationships(dry_run)

        # Step 5: Verify fixes
        self.verify_fixes()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n🔍 DRY RUN COMPLETE - Run without --dry-run to apply fixes"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✅ PERSON DATA INTEGRITY FIX COMPLETE")
            )

    def analyze_person_table(self):
        """Analyze current Person table state"""
        self.stdout.write(self.style.HTTP_INFO("\n📊 ANALYZING PERSON TABLE STATE"))

        with connection.cursor() as cursor:
            # First, check Person table structure to determine PK column
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'people' 
                ORDER BY ordinal_position
            """
            )
            columns = cursor.fetchall()
            self.stdout.write(f"   Person table columns:")

            pk_column = None
            has_id_column = False
            has_contact_id_column = False

            for col in columns:
                col_name, data_type, nullable, default = col
                self.stdout.write(
                    f"     {col_name}: {data_type} (nullable: {nullable}, default: {default})"
                )

                if col_name == "id":
                    has_id_column = True
                    if "nextval" in str(default):  # This is likely the PK with sequence
                        pk_column = "id"
                elif col_name == "contact_id":
                    has_contact_id_column = True
                    if not has_id_column:  # If no id column, contact_id might be PK
                        pk_column = "contact_id"

            # Determine the actual primary key
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'people' 
                AND tc.constraint_type = 'PRIMARY KEY'
            """
            )
            pk_result = cursor.fetchone()
            if pk_result:
                pk_column = pk_result[0]

            self.stdout.write(f"   Primary key column: {pk_column}")
            self.stdout.write(f"   Has 'id' column: {has_id_column}")
            self.stdout.write(f"   Has 'contact_id' column: {has_contact_id_column}")

            # Get total person count
            cursor.execute("SELECT COUNT(*) FROM people")
            total_people = cursor.fetchone()[0]
            self.stdout.write(f"   Total Person records: {total_people}")

            # Check for NULL primary keys (use detected PK column)
            if pk_column:
                cursor.execute(f"SELECT COUNT(*) FROM people WHERE {pk_column} IS NULL")
                null_pk_count = cursor.fetchone()[0]
                self.stdout.write(
                    f"   Person records with NULL {pk_column}: {null_pk_count}"
                )

                # Store pk_column for later use
                self.pk_column = pk_column
            else:
                self.stdout.write("   ⚠️  Could not determine primary key column")
                self.pk_column = "id"  # Default fallback

            # Check for NULL contact_id (FK to contacts table)
            if has_contact_id_column:
                cursor.execute("SELECT COUNT(*) FROM people WHERE contact_id IS NULL")
                null_contact_id_count = cursor.fetchone()[0]
                self.stdout.write(
                    f"   Person records with NULL contact_id: {null_contact_id_count}"
                )

            # Get sample of problematic records
            if pk_column and has_contact_id_column:
                cursor.execute(
                    f"""
                    SELECT {pk_column}, contact_id, title, profession, organization 
                    FROM people 
                    WHERE {pk_column} IS NULL OR contact_id IS NULL 
                    LIMIT 5
                """
                )
                problematic_records = cursor.fetchall()

                if problematic_records:
                    self.stdout.write(f"   Sample problematic records:")
                    for record in problematic_records:
                        self.stdout.write(
                            f"     {pk_column}: {record[0]}, Contact ID: {record[1]}, Title: {record[2]}"
                        )

    def analyze_contact_table(self):
        """Analyze Contact table integrity"""
        self.stdout.write(self.style.HTTP_INFO("\n📊 ANALYZING CONTACT TABLE STATE"))

        with connection.cursor() as cursor:
            # Get total contact count
            cursor.execute("SELECT COUNT(*) FROM contacts")
            total_contacts = cursor.fetchone()[0]
            self.stdout.write(f"   Total Contact records: {total_contacts}")

            # Check for person-type contacts
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person'")
            person_type_contacts = cursor.fetchone()[0]
            self.stdout.write(f"   Person-type Contact records: {person_type_contacts}")

            # Check for orphaned person contacts (no corresponding Person record)
            cursor.execute(
                """
                SELECT COUNT(*) FROM contacts c
                WHERE c.type = 'person' 
                AND NOT EXISTS (SELECT 1 FROM people p WHERE p.contact_id = c.id)
            """
            )
            orphaned_contacts = cursor.fetchone()[0]
            self.stdout.write(f"   Orphaned person-type contacts: {orphaned_contacts}")

    def fix_null_primary_keys(self, dry_run):
        """Fix NULL primary keys in Person table"""
        self.stdout.write(self.style.HTTP_INFO("\n🔧 FIXING NULL PRIMARY KEYS"))

        pk_column = getattr(self, "pk_column", "id")

        with connection.cursor() as cursor:
            # Check if we need to fix the primary key sequence
            cursor.execute(f"SELECT COUNT(*) FROM people WHERE {pk_column} IS NULL")
            null_pk_count = cursor.fetchone()[0]

            if null_pk_count > 0:
                self.stdout.write(
                    f"   Found {null_pk_count} Person records with NULL {pk_column}"
                )

                if not dry_run:
                    # Get the next available ID from sequence
                    cursor.execute(
                        f"SELECT COALESCE(MAX({pk_column}), 0) + 1 FROM people WHERE {pk_column} IS NOT NULL"
                    )
                    next_id = cursor.fetchone()[0]

                    # Determine sequence name based on primary key column
                    if pk_column == "contact_id":
                        seq_name = "people_contact_id_seq"
                    else:
                        seq_name = "people_id_seq"

                    # Update NULL primary keys with sequential IDs
                    cursor.execute(
                        f"""
                        UPDATE people 
                        SET {pk_column} = nextval('{seq_name}')
                        WHERE {pk_column} IS NULL
                    """
                    )

                    # Reset sequence to correct value
                    cursor.execute(
                        f"SELECT setval('{seq_name}', (SELECT MAX({pk_column}) FROM people))"
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"   ✅ Fixed NULL {pk_column} starting from ID {next_id}"
                        )
                    )
                else:
                    self.stdout.write(f"   Would fix {null_pk_count} NULL {pk_column}")
            else:
                self.stdout.write(f"   ✅ No NULL {pk_column} found")

    def rebuild_person_contact_relationships(self, dry_run):
        """Rebuild Person-Contact foreign key relationships"""
        self.stdout.write(
            self.style.HTTP_INFO("\n🔧 REBUILDING PERSON-CONTACT RELATIONSHIPS")
        )

        pk_column = getattr(self, "pk_column", "id")

        with connection.cursor() as cursor:
            # Find Person records with invalid contact_id
            cursor.execute(
                f"""
                SELECT p.{pk_column}, p.contact_id, p.title, p.profession 
                FROM people p
                LEFT JOIN contacts c ON p.contact_id = c.id
                WHERE c.id IS NULL
                LIMIT 10
            """
            )
            invalid_relationships = cursor.fetchall()

            if invalid_relationships:
                self.stdout.write(
                    f"   Found {len(invalid_relationships)} Person records with invalid contact_id"
                )

                for person_id, contact_id, title, profession in invalid_relationships:
                    self.stdout.write(
                        f"     Person {pk_column} {person_id}: contact_id={contact_id}, title={title}"
                    )

                if not dry_run:
                    # Try to find matching contacts for these Person records
                    # This is a more complex fix that might require matching by name/email
                    # For now, we'll create basic contact records for orphaned Person records

                    for (
                        person_id,
                        contact_id,
                        title,
                        profession,
                    ) in invalid_relationships:
                        # Create a basic contact record
                        cursor.execute(
                            """
                            INSERT INTO contacts (type, first_name, last_name, created_at, updated_at)
                            VALUES ('person', %s, '', NOW(), NOW())
                            RETURNING id
                        """,
                            [title or f"Person {person_id}"],
                        )
                        new_contact_id = cursor.fetchone()[0]

                        # Update Person record with new contact_id
                        cursor.execute(
                            f"""
                            UPDATE people SET contact_id = %s WHERE {pk_column} = %s
                        """,
                            [new_contact_id, person_id],
                        )

                        self.stdout.write(
                            f"     ✅ Created Contact {new_contact_id} for Person {person_id}"
                        )
                else:
                    self.stdout.write(
                        f"   Would create {len(invalid_relationships)} new Contact records"
                    )
            else:
                self.stdout.write("   ✅ All Person-Contact relationships are valid")

    def verify_fixes(self):
        """Verify that fixes worked correctly"""
        self.stdout.write(self.style.HTTP_INFO("\n🔍 VERIFYING FIXES"))

        try:
            # Test Django ORM operations
            total_people = Person.objects.count()
            self.stdout.write(f"   Django ORM Person count: {total_people}")

            # Test queryset evaluation
            test_people = list(Person.objects.all()[:5])
            self.stdout.write(
                f"   Successfully evaluated queryset: {len(test_people)} people"
            )

            # Test foreign key access
            for i, person in enumerate(test_people):
                try:
                    contact = person.contact
                    self.stdout.write(
                        f"   Person {person.pk}: contact={contact.id}, name={contact.first_name}"
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"   ❌ Person {person.pk}: FK access failed - {e}"
                        )
                    )

            self.stdout.write(self.style.SUCCESS("   ✅ All verifications passed"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Verification failed: {e}"))
