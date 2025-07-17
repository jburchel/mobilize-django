from django.core.management.base import BaseCommand
from django.db import connection
from mobilize.contacts.models import Person, Contact


class Command(BaseCommand):
    help = "Debug queryset evaluation issue in production"

    def handle(self, *args, **options):
        self.stdout.write("🔍 PRODUCTION: Deep debugging queryset evaluation issue...")

        try:
            # Get raw counts first
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM people;")
                raw_people_count = cursor.fetchone()[0]
                self.stdout.write(f"📊 Raw people count: {raw_people_count}")

                cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person';")
                raw_contacts_count = cursor.fetchone()[0]
                self.stdout.write(f"📊 Raw person contacts count: {raw_contacts_count}")

                # Check people table structure
                cursor.execute(
                    """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'people'
                    ORDER BY ordinal_position;
                """
                )
                people_columns = cursor.fetchall()
                self.stdout.write(f"📋 People table columns:")
                for col_name, col_type in people_columns:
                    self.stdout.write(f"   {col_name}: {col_type}")

                # Check if there are any NULL contact_ids
                cursor.execute("SELECT COUNT(*) FROM people WHERE contact_id IS NULL;")
                null_contact_ids = cursor.fetchone()[0]
                self.stdout.write(f"📊 People with NULL contact_id: {null_contact_ids}")

                # Check sample records with problematic data
                cursor.execute(
                    """
                    SELECT contact_id, title, profession, organization
                    FROM people 
                    ORDER BY contact_id
                    LIMIT 10;
                """
                )
                raw_samples = cursor.fetchall()
                self.stdout.write(f"📋 Sample people records (first 10):")
                for contact_id, title, profession, organization in raw_samples:
                    self.stdout.write(
                        f"   contact_id={contact_id}, title={title}, profession={profession}, org={organization}"
                    )

            # Test Django ORM step by step
            self.stdout.write(f"\n🔧 Testing Django ORM step by step...")

            # Step 1: Basic Person queryset
            people_basic = Person.objects.all()
            basic_count = people_basic.count()
            self.stdout.write(f"1. Person.objects.all().count(): {basic_count}")

            # Step 2: Test first person access
            try:
                first_person = people_basic.first()
                if first_person:
                    self.stdout.write(
                        f"2. First person: PK={first_person.pk}, Contact ID={first_person.contact_id}"
                    )
                    self.stdout.write(f"   Has ID attr: {hasattr(first_person, 'id')}")

                    # Test contact access
                    try:
                        contact = first_person.contact
                        self.stdout.write(
                            f"   Contact: {contact.first_name} {contact.last_name}"
                        )
                    except Exception as e:
                        self.stdout.write(f"   ❌ Error accessing contact: {e}")
                else:
                    self.stdout.write(
                        f"2. ❌ No first person found despite count={basic_count}"
                    )
            except Exception as e:
                self.stdout.write(f"2. ❌ Error getting first person: {e}")

            # Step 3: Test queryset slicing
            try:
                self.stdout.write(f"3. Testing queryset slicing...")
                people_slice = people_basic[:5]
                self.stdout.write(f"   Slice created successfully")

                people_list = list(people_slice)
                self.stdout.write(f"   Converted to list: {len(people_list)} items")

                for i, person in enumerate(people_list[:3]):
                    self.stdout.write(f"   Person {i+1}: PK={person.pk}")

            except Exception as e:
                self.stdout.write(f"3. ❌ Error with queryset slicing: {e}")
                import traceback

                self.stdout.write(f"   Full traceback: {traceback.format_exc()}")

            # Step 4: Test the exact API queryset
            self.stdout.write(f"\n🎯 Testing exact API queryset...")
            try:
                people = Person.objects.select_related(
                    "contact", "contact__office", "primary_church"
                ).prefetch_related("contact__pipeline_entries__current_stage")
                api_count = people.count()
                self.stdout.write(f"4. API queryset count: {api_count}")

                people_ordered = people.order_by("-pk")
                ordered_count = people_ordered.count()
                self.stdout.write(f"5. With order_by('-pk'): {ordered_count}")

                # Test slicing the exact API queryset
                try:
                    api_slice = people_ordered[:3]
                    api_list = list(api_slice)
                    self.stdout.write(f"6. API queryset sliced: {len(api_list)} items")

                    for i, person in enumerate(api_list):
                        self.stdout.write(f"   API Person {i+1}: PK={person.pk}")

                except Exception as e:
                    self.stdout.write(f"6. ❌ Error with API queryset slicing: {e}")
                    import traceback

                    self.stdout.write(f"   Full traceback: {traceback.format_exc()}")

            except Exception as e:
                self.stdout.write(f"4-6. ❌ Error with API queryset: {e}")
                import traceback

                self.stdout.write(f"   Full traceback: {traceback.format_exc()}")

            # Step 5: Test individual components
            self.stdout.write(f"\n🔍 Testing individual relationship components...")

            try:
                # Test without prefetch_related
                people_no_prefetch = Person.objects.select_related(
                    "contact", "contact__office", "primary_church"
                )
                no_prefetch_count = people_no_prefetch.count()
                self.stdout.write(f"7. Without prefetch_related: {no_prefetch_count}")

                no_prefetch_list = list(people_no_prefetch[:3])
                self.stdout.write(
                    f"   Converted to list: {len(no_prefetch_list)} items"
                )

            except Exception as e:
                self.stdout.write(f"7. ❌ Error without prefetch_related: {e}")

            try:
                # Test without primary_church
                people_no_church = Person.objects.select_related(
                    "contact", "contact__office"
                )
                no_church_count = people_no_church.count()
                self.stdout.write(f"8. Without primary_church: {no_church_count}")

                no_church_list = list(people_no_church[:3])
                self.stdout.write(f"   Converted to list: {len(no_church_list)} items")

            except Exception as e:
                self.stdout.write(f"8. ❌ Error without primary_church: {e}")

            try:
                # Test with only contact
                people_basic_related = Person.objects.select_related("contact")
                basic_related_count = people_basic_related.count()
                self.stdout.write(
                    f"9. Only select_related('contact'): {basic_related_count}"
                )

                basic_related_list = list(people_basic_related[:3])
                self.stdout.write(
                    f"   Converted to list: {len(basic_related_list)} items"
                )

            except Exception as e:
                self.stdout.write(f"9. ❌ Error with basic select_related: {e}")

        except Exception as e:
            self.stdout.write(f"❌ Overall Error: {e}")
            import traceback

            self.stdout.write(f"Full traceback: {traceback.format_exc()}")
