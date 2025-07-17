"""
Load testing for Mobilize CRM using locust
This file can be run with: locust -f test_load_testing.py --host=http://localhost:8000
"""

import random
import string
from locust import HttpUser, task, between
from locust.exception import RescheduleTask


class MobilizeCRMUser(HttpUser):
    """Simulated user for load testing Mobilize CRM"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Login when user starts"""
        # Create a unique username for this user
        self.username = f"loadtest_{random.randint(1000, 9999)}"
        self.password = "loadtestpass123"

        # In a real test, you'd create the user first or use existing test users
        # For now, we'll use a predefined test user
        self.username = "loadtestuser"
        self.password = "loadtestpass123"

        # Login
        response = self.client.post(
            "/auth/login/", {"username": self.username, "password": self.password}
        )

        if response.status_code != 200:
            print(f"Login failed for user {self.username}")
            raise RescheduleTask()

    @task(3)
    def view_dashboard(self):
        """View the main dashboard"""
        self.client.get("/dashboard/", name="Dashboard")

    @task(5)
    def view_contact_list(self):
        """View contact list with pagination"""
        page = random.randint(1, 10)
        self.client.get(f"/contacts/?page={page}", name="Contact List")

    @task(4)
    def search_contacts(self):
        """Search for contacts"""
        search_terms = ["John", "Smith", "test", "contact", "lead"]
        search = random.choice(search_terms)
        self.client.get(f"/contacts/?search={search}", name="Contact Search")

    @task(2)
    def view_contact_detail(self):
        """View a specific contact detail"""
        contact_id = random.randint(1, 100)  # Assuming we have contacts 1-100
        self.client.get(f"/contacts/{contact_id}/", name="Contact Detail")

    @task(3)
    def view_task_list(self):
        """View task list"""
        self.client.get("/tasks/", name="Task List")

    @task(2)
    def view_pending_tasks(self):
        """View pending tasks only"""
        self.client.get("/tasks/?status=pending", name="Pending Tasks")

    @task(1)
    def create_contact(self):
        """Create a new contact"""
        first_name = "".join(random.choices(string.ascii_letters, k=6))
        last_name = "".join(random.choices(string.ascii_letters, k=8))

        self.client.post(
            "/contacts/create/",
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
                "phone": f"555-{random.randint(1000, 9999)}",
                "pipeline_stage": random.choice(["New Lead", "Contacted", "Qualified"]),
                "priority": random.choice(["low", "medium", "high"]),
            },
            name="Create Contact",
        )

    @task(2)
    def view_communication_list(self):
        """View communication history"""
        self.client.get("/communications/", name="Communication List")

    @task(1)
    def view_churches(self):
        """View church list"""
        self.client.get("/churches/", name="Church List")

    @task(1)
    def view_pipeline(self):
        """View pipeline visualization"""
        self.client.get("/pipeline/", name="Pipeline View")

    def on_stop(self):
        """Logout when user stops"""
        self.client.post("/auth/logout/", name="Logout")


class AdminUser(HttpUser):
    """Simulated admin user with different behavior patterns"""

    wait_time = between(2, 5)  # Admins might take longer between actions

    def on_start(self):
        """Login as admin"""
        self.username = "adminuser"
        self.password = "adminpass123"

        response = self.client.post(
            "/auth/login/", {"username": self.username, "password": self.password}
        )

        if response.status_code != 200:
            print("Admin login failed")
            raise RescheduleTask()

    @task(2)
    def view_dashboard(self):
        """View admin dashboard"""
        self.client.get("/dashboard/", name="Admin Dashboard")

    @task(3)
    def view_all_users(self):
        """View user management page"""
        self.client.get("/admin/users/", name="User Management")

    @task(2)
    def view_office_management(self):
        """View office management"""
        self.client.get("/admin/offices/", name="Office Management")

    @task(1)
    def generate_report(self):
        """Generate a report"""
        report_types = ["contact", "task", "communication", "pipeline"]
        report_type = random.choice(report_types)
        self.client.get(
            f"/reports/{report_type}/", name=f"{report_type.title()} Report"
        )

    @task(2)
    def bulk_operations(self):
        """Perform bulk operations"""
        self.client.get("/contacts/?bulk=true", name="Bulk Contact View")

    @task(1)
    def view_settings(self):
        """View system settings"""
        self.client.get("/settings/", name="System Settings")


class MobileUser(HttpUser):
    """Simulated mobile user with limited actions"""

    wait_time = between(3, 8)  # Mobile users might be slower

    def on_start(self):
        """Login as mobile user"""
        self.username = "mobileuser"
        self.password = "mobilepass123"

        # Set mobile user agent
        self.client.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            }
        )

        response = self.client.post(
            "/auth/login/", {"username": self.username, "password": self.password}
        )

        if response.status_code != 200:
            print("Mobile login failed")
            raise RescheduleTask()

    @task(5)
    def view_dashboard_mobile(self):
        """View mobile dashboard"""
        self.client.get("/dashboard/", name="Mobile Dashboard")

    @task(3)
    def view_today_tasks(self):
        """View today's tasks"""
        self.client.get("/tasks/?due=today", name="Today's Tasks")

    @task(2)
    def quick_contact_lookup(self):
        """Quick contact lookup"""
        contact_id = random.randint(1, 50)
        self.client.get(f"/contacts/{contact_id}/", name="Mobile Contact View")

    @task(1)
    def add_quick_note(self):
        """Add a quick note to a contact"""
        contact_id = random.randint(1, 50)
        self.client.post(
            f"/contacts/{contact_id}/note/",
            {
                "note": f"Quick note added at {random.randint(1, 12)}:{random.randint(10, 59)}"
            },
            name="Add Quick Note",
        )


# Scenario-based load testing
class NewUserOnboardingScenario(HttpUser):
    """Simulate new user onboarding flow"""

    wait_time = between(2, 4)

    def on_start(self):
        """Start onboarding flow"""
        self.step = 0
        self.contact_id = None

        # Login as new user
        self.username = "newuser"
        self.password = "newuserpass123"

        response = self.client.post(
            "/auth/login/", {"username": self.username, "password": self.password}
        )

        if response.status_code != 200:
            print("New user login failed")
            raise RescheduleTask()

    @task
    def onboarding_flow(self):
        """Execute onboarding steps in sequence"""

        if self.step == 0:
            # View dashboard for first time
            self.client.get("/dashboard/", name="First Dashboard View")
            self.step = 1

        elif self.step == 1:
            # Create first contact
            response = self.client.post(
                "/contacts/create/",
                {
                    "first_name": "First",
                    "last_name": "Contact",
                    "email": "first.contact@example.com",
                    "phone": "555-0001",
                },
                name="Create First Contact",
            )

            # Extract contact ID from response (in real scenario)
            self.contact_id = 1  # Placeholder
            self.step = 2

        elif self.step == 2:
            # Create first task
            self.client.post(
                "/tasks/create/",
                {
                    "title": "Follow up with first contact",
                    "description": "Initial follow-up",
                    "due_date": "2025-07-01",
                    "contact_id": self.contact_id,
                    "priority": "high",
                },
                name="Create First Task",
            )
            self.step = 3

        elif self.step == 3:
            # View contact list
            self.client.get("/contacts/", name="View Contacts After Creation")
            self.step = 4

        elif self.step == 4:
            # Complete onboarding
            self.client.get("/dashboard/", name="Return to Dashboard")
            self.step = 0  # Reset to start


# Stress testing scenario
class StressTestUser(HttpUser):
    """User that performs rapid, intensive operations"""

    wait_time = between(0.1, 0.5)  # Very short wait times

    def on_start(self):
        """Quick login"""
        self.client.post(
            "/auth/login/", {"username": "stressuser", "password": "stresspass123"}
        )

    @task(10)
    def rapid_search(self):
        """Rapid search queries"""
        chars = string.ascii_lowercase
        search = "".join(random.choices(chars, k=random.randint(1, 3)))
        self.client.get(f"/contacts/?search={search}", name="Rapid Search")

    @task(5)
    def rapid_navigation(self):
        """Rapid page navigation"""
        pages = ["/dashboard/", "/contacts/", "/tasks/", "/communications/"]
        page = random.choice(pages)
        self.client.get(page, name="Rapid Navigation")

    @task(3)
    def concurrent_updates(self):
        """Simulate concurrent updates"""
        contact_id = random.randint(1, 10)
        self.client.post(
            f"/contacts/{contact_id}/update/",
            {"notes": f"Updated at {random.random()}"},
            name="Concurrent Update",
        )


# API Load Testing (if API endpoints exist)
class APIUser(HttpUser):
    """Test API endpoints"""

    wait_time = between(0.5, 2)

    def on_start(self):
        """Get API token"""
        response = self.client.post(
            "/api/auth/token/", {"username": "apiuser", "password": "apipass123"}
        )

        if response.status_code == 200:
            self.token = response.json().get("token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(5)
    def api_get_contacts(self):
        """GET contacts via API"""
        self.client.get("/api/contacts/", name="API Get Contacts")

    @task(3)
    def api_get_contact_detail(self):
        """GET specific contact via API"""
        contact_id = random.randint(1, 100)
        self.client.get(f"/api/contacts/{contact_id}/", name="API Get Contact")

    @task(2)
    def api_create_contact(self):
        """POST new contact via API"""
        self.client.post(
            "/api/contacts/",
            json={
                "first_name": f"API{random.randint(1000, 9999)}",
                "last_name": "Test",
                "email": f"api{random.randint(1000, 9999)}@example.com",
            },
            name="API Create Contact",
        )

    @task(1)
    def api_update_contact(self):
        """PUT update contact via API"""
        contact_id = random.randint(1, 50)
        self.client.put(
            f"/api/contacts/{contact_id}/",
            json={"notes": f"Updated via API at {random.random()}"},
            name="API Update Contact",
        )
