import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker

from mobilize.admin_panel.models import Office, UserOffice
from mobilize.authentication.models import User
from mobilize.contacts.models import Person, Contact
from mobilize.churches.models import Church, ChurchMembership
from mobilize.tasks.models import Task
from mobilize.communications.models import Communication
from mobilize.pipeline.models import Pipeline, PipelineStage, PipelineContact

fake = Faker()


class Command(BaseCommand):
    help = "Create comprehensive sample data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--churches",
            type=int,
            default=50,
            help="Number of churches to create (default: 50)",
        )
        parser.add_argument(
            "--people",
            type=int,
            default=100,
            help="Number of people to create (default: 100)",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm that you want to create sample data",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "This will create sample data in your database.\n"
                    "Run with --confirm to proceed.\n"
                    f'Will create: {options["churches"]} churches, {options["people"]} people, plus users, tasks, and communications.'
                )
            )
            return

        with transaction.atomic():
            self.stdout.write("Creating sample data...")

            # Create offices
            offices = self.create_offices()

            # Create users
            users = self.create_users(offices)

            # Create churches
            churches = self.create_churches(options["churches"], offices, users)

            # Create people
            people = self.create_people(options["people"], offices, users)

            # Create church memberships
            self.create_church_memberships(people, churches)

            # Update church primary contact information
            self.update_church_primary_contacts(churches)

            # Create tasks
            self.create_tasks(people, churches, users, offices)

            # Create communications
            self.create_communications(people, churches, users, offices)

            # Set up pipeline data
            self.setup_pipeline_data(people, churches)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created sample data:\n"
                f"- {len(offices)} offices\n"
                f"- {len(users)} users\n"
                f'- {options["churches"]} churches\n'
                f'- {options["people"]} people\n'
                f"- Tasks, communications, and pipeline data"
            )
        )

    def create_offices(self):
        """Create sample offices"""
        offices_data = [
            {
                "name": "North America Office",
                "code": "NA",
                "city": "Dallas",
                "state": "TX",
                "country": "USA",
            },
            {"name": "Europe Office", "code": "EU", "city": "London", "country": "UK"},
            {
                "name": "Asia Pacific Office",
                "code": "AP",
                "city": "Singapore",
                "country": "Singapore",
            },
            {
                "name": "Latin America Office",
                "code": "LA",
                "city": "Mexico City",
                "country": "Mexico",
            },
        ]

        offices = []
        for office_data in offices_data:
            office, created = Office.objects.get_or_create(
                name=office_data["name"], defaults=office_data
            )
            offices.append(office)
            if created:
                self.stdout.write(f"Created office: {office.name}")

        return offices

    def create_users(self, offices):
        """Create sample users with different roles"""
        users = []

        # Create super admin
        super_admin, created = User.objects.get_or_create(
            email="admin@mobilize.com",
            defaults={
                "username": "admin",
                "first_name": "Super",
                "last_name": "Admin",
                "role": "super_admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            super_admin.set_password("admin123")
            super_admin.save()
            self.stdout.write(f"Created super admin: {super_admin.email}")

        # Assign super admin to first office
        UserOffice.objects.get_or_create(
            user=super_admin, office=offices[0], defaults={"is_primary": True}
        )
        users.append(super_admin)

        # Create office admins
        for i, office in enumerate(offices):
            office_admin, created = User.objects.get_or_create(
                email=f'admin.{office.name.lower().replace(" ", ".")}@mobilize.com',
                defaults={
                    "username": f'admin_{office.name.lower().replace(" ", "_")}',
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "role": "office_admin",
                    "is_staff": True,
                },
            )
            if created:
                office_admin.set_password("admin123")
                office_admin.save()
                self.stdout.write(f"Created office admin: {office_admin.email}")

            # Assign office admin to their office
            UserOffice.objects.get_or_create(
                user=office_admin, office=office, defaults={"is_primary": True}
            )
            users.append(office_admin)

        # Create standard users
        for i in range(12):  # 3 per office
            office = offices[i % len(offices)]
            user, created = User.objects.get_or_create(
                email=f"user{i+1}@mobilize.com",
                defaults={
                    "username": f"user{i+1}",
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "role": "standard_user",
                },
            )
            if created:
                user.set_password("user123")
                user.save()
                self.stdout.write(f"Created user: {user.email}")

            # Assign user to their office
            UserOffice.objects.get_or_create(
                user=user, office=office, defaults={"is_primary": True}
            )
            users.append(user)

        return users

    def create_churches(self, count, offices, users):
        """Create sample churches"""
        churches = []

        church_names = [
            "First Baptist Church",
            "Grace Community Church",
            "New Life Fellowship",
            "Cornerstone Church",
            "Harvest Christian Center",
            "Faith Bible Church",
            "Trinity Methodist Church",
            "Hope Presbyterian Church",
            "Victory Chapel",
            "Crossroads Church",
            "Lighthouse Baptist Church",
            "River of Life Church",
            "Emmanuel Church",
            "Calvary Chapel",
            "Bethel Assembly of God",
            "Christ the King Church",
            "Redeemer Lutheran Church",
            "Sacred Heart Church",
            "Unity Fellowship",
            "Abundant Life Church",
            "Mountain View Church",
            "Valley Christian Center",
            "Sunrise Baptist Church",
            "Peace Lutheran Church",
            "Joy Christian Fellowship",
            "Rock Church",
            "Living Water Church",
            "New Hope Baptist Church",
            "Grace Point Church",
            "Freedom Church",
            "Restoration Church",
            "The Bridge Church",
            "Elevation Church",
            "Journey Church",
            "Mosaic Church",
            "Catalyst Church",
            "Impact Church",
            "Overflow Church",
            "Anchor Church",
            "Compass Church",
            "Refuge Church",
            "Sanctuary Church",
            "Harbor Church",
            "Oasis Church",
            "Vineyard Church",
            "Gateway Church",
            "Pathway Church",
            "Summit Church",
            "Horizon Church",
        ]

        denominations = [
            "Baptist",
            "Methodist",
            "Presbyterian",
            "Pentecostal",
            "Lutheran",
            "Non-denominational",
            "Assembly of God",
            "Episcopal",
            "Catholic",
            "Evangelical",
            "Reformed",
            "Mennonite",
            "Nazarene",
            "Wesleyan",
            "Church of Christ",
            "Disciples of Christ",
            "Adventist",
            "Quaker",
        ]

        size_categories = ["small", "medium", "large", "mega"]
        size_weights = [40, 35, 20, 5]  # Most churches are small to medium

        for i in range(count):
            # Create contact first
            city = fake.city()
            state = fake.state_abbr()

            contact = Contact.objects.create(
                type="church",
                church_name=f"{random.choice(church_names)} of {city}",
                email=fake.email(),
                phone=fake.phone_number()[:20],
                street_address=fake.street_address(),
                city=city,
                state=state,
                zip_code=fake.zipcode(),
                country="USA",
                priority=random.choice(["low", "medium", "high"]),
                status=random.choice(
                    ["active", "active", "active", "inactive"]
                ),  # 75% active
                notes=fake.text(max_nb_chars=200),
                user=random.choice(users),
                office=random.choice(offices),
            )

            church_name = contact.church_name
            denomination = random.choice(denominations)
            size_category = random.choices(size_categories, weights=size_weights)[0]

            # Set congregation size based on category
            if size_category == "small":
                congregation_size = random.randint(25, 200)
                weekly_attendance = int(congregation_size * random.uniform(0.6, 0.8))
            elif size_category == "medium":
                congregation_size = random.randint(200, 800)
                weekly_attendance = int(congregation_size * random.uniform(0.7, 0.9))
            elif size_category == "large":
                congregation_size = random.randint(800, 2000)
                weekly_attendance = int(congregation_size * random.uniform(0.8, 0.95))
            else:  # mega
                congregation_size = random.randint(2000, 10000)
                weekly_attendance = int(congregation_size * random.uniform(0.85, 0.95))

            church = Church.objects.create(
                contact=contact,
                name=church_name,
                denomination=denomination,
                website=f"www.{church_name.lower().replace(' ', '').replace('of', '')}.org",
                year_founded=random.randint(1950, 2020),
                congregation_size=congregation_size,
                weekly_attendance=weekly_attendance,
                service_times={
                    "sunday_morning": f"{random.choice(['8:30', '9:00', '9:30', '10:00', '10:30', '11:00'])} AM",
                    "sunday_evening": (
                        f"{random.choice(['5:00', '5:30', '6:00', '6:30', '7:00'])} PM"
                        if random.choice([True, False])
                        else None
                    ),
                    "wednesday": (
                        f"{random.choice(['6:30', '7:00', '7:30'])} PM"
                        if random.choice([True, False])
                        else None
                    ),
                },
                facilities={
                    "sanctuary_capacity": congregation_size,
                    "parking_spaces": int(congregation_size * random.uniform(0.3, 0.6)),
                    "classrooms": random.randint(5, 25),
                    "fellowship_hall": random.choice([True, False]),
                    "gym": (
                        random.choice([True, False])
                        if size_category in ["medium", "large", "mega"]
                        else False
                    ),
                },
                ministries=[
                    random.choice(
                        [
                            "Youth Ministry",
                            "Children's Ministry",
                            "Women's Ministry",
                            "Men's Ministry",
                        ]
                    ),
                    random.choice(
                        [
                            "Worship Ministry",
                            "Missions Ministry",
                            "Small Groups",
                            "Outreach Ministry",
                        ]
                    ),
                    random.choice(
                        [
                            "Senior Ministry",
                            "Young Adults",
                            "Marriage Ministry",
                            "Recovery Ministry",
                        ]
                    ),
                ][: random.randint(2, 4)],
                primary_language="English",
                secondary_languages=(
                    [
                        random.choice(
                            ["Spanish", "Korean", "Chinese", "Portuguese", "French"]
                        )
                    ]
                    if random.choice([True, False, False])
                    else None
                ),
                pastor_name=fake.name(),
                pastor_email=fake.email(),
                pastor_phone=fake.phone_number()[:20],
            )
            churches.append(church)

            if i % 10 == 0:
                self.stdout.write(f"Created {i+1} churches...")

        return churches

    def create_people(self, count, offices, users):
        """Create sample people"""
        people = []

        for i in range(count):
            # Create contact first
            first_name = fake.first_name()
            last_name = fake.last_name()

            contact = Contact.objects.create(
                type="person",
                first_name=first_name,
                last_name=last_name,
                email=fake.email(),
                phone=fake.phone_number()[:20],
                street_address=fake.street_address(),
                city=fake.city(),
                state=fake.state_abbr(),
                zip_code=fake.zipcode(),
                country="USA",
                priority=random.choice(["low", "medium", "high"]),
                status=random.choice(
                    ["active", "active", "active", "inactive"]
                ),  # 75% active
                notes=fake.text(max_nb_chars=200),
                user=random.choice(users),
                office=random.choice(offices),
            )

            person = Person.objects.create(
                contact=contact,
                birthday=fake.date_of_birth(minimum_age=18, maximum_age=80),
                marital_status=random.choice(
                    ["single", "married", "divorced", "widowed"]
                ),
                profession=fake.job(),
                organization=fake.company(),
                home_country="USA",
                languages=(
                    ["English"]
                    if random.choice([True, False, False])
                    else [
                        "English",
                        random.choice(
                            ["Spanish", "French", "German", "Korean", "Chinese"]
                        ),
                    ]
                ),
                linkedin_url=(
                    f"https://linkedin.com/in/{first_name.lower()}{last_name.lower()}"
                    if random.choice([True, False, False])
                    else None
                ),
            )
            people.append(person)

            if i % 20 == 0:
                self.stdout.write(f"Created {i+1} people...")

        return people

    def create_church_memberships(self, people, churches):
        """Create relationships between people and churches"""
        memberships = []

        # First, ensure each church has a primary contact
        for church in churches:
            # Select a person to be the primary contact (could be pastor or other leader)
            available_people = [
                p
                for p in people
                if not p.church_memberships.filter(church=church).exists()
            ]
            if available_people:
                primary_person = random.choice(available_people)

                # Decide if they should be a pastor or other primary contact
                is_pastor = random.choice([True, False])  # 50% chance of being a pastor

                if is_pastor:
                    role = random.choice(
                        ["senior_pastor", "associate_pastor", "missions_pastor"]
                    )
                else:
                    role = random.choice(
                        [
                            "elder",
                            "deacon",
                            "board_member",
                            "ministry_leader",
                            "secretary",
                        ]
                    )

                membership = ChurchMembership.objects.create(
                    person=primary_person,
                    church=church,
                    role=role,
                    is_primary_contact=True,
                    start_date=fake.date_between(start_date="-5y", end_date="today"),
                    status="active",
                    notes=f"Primary contact for {church.name}",
                )
                memberships.append(membership)

        # Then assign additional people to churches (about 60% of remaining people)
        remaining_people = [p for p in people if not p.church_memberships.exists()]
        people_to_assign = random.sample(
            remaining_people, min(int(len(people) * 0.6), len(remaining_people))
        )

        for person in people_to_assign:
            church = random.choice(churches)

            # Don't create duplicate memberships
            if not ChurchMembership.objects.filter(
                person=person, church=church
            ).exists():
                # Choose appropriate role (most should be regular members)
                role_weights = {
                    "member": 60,
                    "regular_attendee": 20,
                    "volunteer": 10,
                    "committee_member": 5,
                    "ministry_leader": 3,
                    "deacon": 1,
                    "elder": 1,
                }

                roles = list(role_weights.keys())
                weights = list(role_weights.values())
                role = random.choices(roles, weights=weights)[0]

                membership = ChurchMembership.objects.create(
                    person=person,
                    church=church,
                    role=role,
                    is_primary_contact=False,
                    start_date=fake.date_between(start_date="-5y", end_date="today"),
                    status=random.choice(
                        ["active", "active", "active", "inactive"]
                    ),  # 75% active
                )
                memberships.append(membership)

        self.stdout.write(f"Created {len(memberships)} church memberships")
        self.stdout.write(f"All {len(churches)} churches now have primary contacts")

    def update_church_primary_contacts(self, churches):
        """Update church records with primary contact information"""
        updated_count = 0

        for church in churches:
            primary_contact = church.get_primary_contact()
            if primary_contact:
                church.primary_contact_first_name = primary_contact.contact.first_name
                church.primary_contact_last_name = primary_contact.contact.last_name
                church.primary_contact_email = primary_contact.contact.email
                church.primary_contact_phone = primary_contact.contact.phone
                church.save()
                updated_count += 1

        self.stdout.write(
            f"Updated primary contact information for {updated_count} churches"
        )

    def create_tasks(self, people, churches, users, offices):
        """Create sample tasks"""
        tasks = []

        task_titles = [
            "Follow up on visit",
            "Send welcome package",
            "Schedule meeting",
            "Prepare presentation",
            "Review partnership proposal",
            "Make phone call",
            "Send thank you note",
            "Update contact information",
            "Plan event",
            "Coordinate volunteers",
            "Prepare materials",
            "Schedule training",
            "Send partnership agreement",
            "Organize mission trip",
            "Plan fundraising event",
            "Coordinate youth program",
            "Schedule pastor meeting",
            "Prepare ministry materials",
            "Follow up on donation",
            "Plan outreach event",
            "Coordinate volunteer training",
            "Send quarterly report",
            "Schedule church visit",
            "Prepare budget proposal",
            "Organize leadership retreat",
            "Plan community service",
            "Coordinate worship team",
            "Send ministry update",
            "Schedule board meeting",
            "Plan evangelism training",
            "Coordinate missions conference",
            "Prepare annual report",
            "Plan stewardship campaign",
        ]

        for i in range(150):  # Create 150 tasks
            # Randomly assign to person or church
            if random.choice([True, False]):
                person = random.choice(people)
                church = None
            else:
                person = None
                church = random.choice(churches)

            due_date = fake.date_between(start_date="-30d", end_date="+60d")
            status = random.choice(["pending", "in_progress", "completed", "cancelled"])

            task = Task.objects.create(
                title=random.choice(task_titles),
                description=fake.text(max_nb_chars=250),
                due_date=due_date,
                priority=random.choice(["low", "medium", "high"]),
                status=status,
                person=person,
                church=church,
                assigned_to=random.choice(users),
                created_by=random.choice(users),
                office=random.choice(offices),
                completed_at=(
                    fake.date_time_between(start_date=due_date, end_date="now")
                    if status == "completed"
                    else None
                ),
            )
            tasks.append(task)

        self.stdout.write(f"Created {len(tasks)} tasks")

    def create_communications(self, people, churches, users, offices):
        """Create sample communications"""
        communications = []

        communication_types = ["email", "phone", "meeting", "letter", "text"]
        subjects = [
            "Partnership Discussion",
            "Follow-up Meeting",
            "Thank You",
            "Event Invitation",
            "Resource Sharing",
            "Prayer Request",
            "Volunteer Opportunity",
            "Ministry Update",
            "Support Request",
            "Mission Trip Information",
            "Youth Program Details",
            "Fundraising Campaign",
            "Leadership Training",
            "Community Outreach",
            "Worship Service Planning",
            "Budget Discussion",
            "Facility Needs",
            "Staff Meeting",
            "Evangelism Training",
            "Discipleship Program",
            "Small Group Coordination",
            "Missions Conference",
            "Stewardship Teaching",
            "Church Planting",
            "Pastoral Care",
            "Counseling Services",
            "Marriage Ministry",
            "Children's Ministry",
            "Senior Adult Ministry",
            "Recovery Program",
        ]

        for i in range(200):  # Create 200 communications
            # Randomly assign to person or church
            if random.choice([True, False]):
                person = random.choice(people)
                church = None
            else:
                person = None
                church = random.choice(churches)

            comm = Communication.objects.create(
                type=random.choice(communication_types),
                subject=random.choice(subjects),
                content=fake.text(max_nb_chars=250),
                date=fake.date_time_between(start_date="-90d", end_date="now"),
                person=person,
                church=church,
                user=random.choice(users),
                office=random.choice(offices),
            )
            communications.append(comm)

        self.stdout.write(f"Created {len(communications)} communications")

    def setup_pipeline_data(self, people, churches):
        """Set up pipeline stages and assign contacts to stages"""
        from mobilize.pipeline.models import (
            MAIN_PEOPLE_PIPELINE_STAGES,
            MAIN_CHURCH_PIPELINE_STAGES,
        )

        # Get or create main pipelines
        people_pipeline, _ = Pipeline.objects.get_or_create(
            name="Main People Pipeline",
            pipeline_type="people",
            is_main_pipeline=True,
            defaults={"description": "Main pipeline for tracking people"},
        )

        church_pipeline, _ = Pipeline.objects.get_or_create(
            name="Main Church Pipeline",
            pipeline_type="church",
            is_main_pipeline=True,
            defaults={"description": "Main pipeline for tracking churches"},
        )

        # Create pipeline stages for people
        people_stages = []
        for i, (stage_code, stage_name) in enumerate(MAIN_PEOPLE_PIPELINE_STAGES):
            stage, _ = PipelineStage.objects.get_or_create(
                pipeline=people_pipeline,
                name=stage_name,
                defaults={"order": i + 1, "description": f"{stage_name} stage"},
            )
            people_stages.append(stage)

        # Create pipeline stages for churches
        church_stages = []
        for i, (stage_code, stage_name) in enumerate(MAIN_CHURCH_PIPELINE_STAGES):
            stage, _ = PipelineStage.objects.get_or_create(
                pipeline=church_pipeline,
                name=stage_name,
                defaults={"order": i + 1, "description": f"{stage_name} stage"},
            )
            church_stages.append(stage)

        # Assign people to pipeline stages
        for person in people:
            stage = random.choice(people_stages)
            PipelineContact.objects.get_or_create(
                contact=person.contact,
                pipeline=people_pipeline,
                current_stage=stage,
                contact_type="person",
                defaults={
                    "entered_at": fake.date_time_between(
                        start_date="-90d", end_date="now"
                    )
                },
            )

        # Assign churches to pipeline stages
        for church in churches:
            stage = random.choice(church_stages)
            PipelineContact.objects.get_or_create(
                contact=church.contact,
                pipeline=church_pipeline,
                current_stage=stage,
                contact_type="church",
                defaults={
                    "entered_at": fake.date_time_between(
                        start_date="-90d", end_date="now"
                    )
                },
            )

        self.stdout.write("Set up pipeline data for all contacts")
