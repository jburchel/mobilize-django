"""
Response time measurement and optimization tests for Mobilize CRM
"""

import time
import cProfile
import pstats
import io
from functools import wraps
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, reset_queries
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from mobilize.contacts.models import Contact, Person
from mobilize.churches.models import Church
from mobilize.tasks.models import Task
from mobilize.communications.models import Communication
from mobilize.admin_panel.models import Office, UserOffice

User = get_user_model()


def measure_time(func):
    """Decorator to measure function execution time"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result

    return wrapper


def profile_view(func):
    """Decorator to profile view performance"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()

        # Print profiling results
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        ps.print_stats(20)  # Print top 20 time-consuming functions
        print(s.getvalue())

        return result

    return wrapper


class ResponseTimeOptimizationTest(TestCase):
    """Test and optimize response times for critical views"""

    def setUp(self):
        self.client = Client()
        self.office = Office.objects.create(
            name="Optimization Office", code="OPT", is_active=True
        )

        self.user = User.objects.create_user(
            username="optuser",
            email="opt@example.com",
            password="optpass123",
            role="standard_user",
        )

        UserOffice.objects.create(user=self.user, office=self.office)

        # Create test data
        self._create_test_data()

    def _create_test_data(self):
        """Create test data for optimization testing"""
        # Create contacts
        for i in range(100):
            contact = Contact.objects.create(
                type="person",
                first_name=f"Opt{i}",
                last_name=f"Test{i}",
                email=f"opt{i}@example.com",
                user=self.user,
                office=self.office,
            )
            Person.objects.create(contact=contact)

            # Create tasks
            if i % 2 == 0:
                Task.objects.create(
                    title=f"Task for Opt{i}",
                    due_date=timezone.now().date() + timedelta(days=i % 30),
                    assigned_to=self.user,
                    created_by=self.user,
                    contact=contact,
                    status="pending",
                )

            # Create communications
            if i % 3 == 0:
                Communication.objects.create(
                    type="email",
                    subject=f"Email for Opt{i}",
                    message="Test message",
                    direction="outbound",
                    date=timezone.now().date(),
                    contact=contact,
                    user=self.user,
                )

    @measure_time
    def test_dashboard_response_time(self):
        """Measure and optimize dashboard response time"""
        self.client.login(username="optuser", password="optpass123")

        # Clear queries
        reset_queries()

        # Measure response time
        start_time = time.time()
        response = self.client.get(reverse("core:dashboard"))
        end_time = time.time()

        self.assertEqual(response.status_code, 200)

        # Analyze queries
        query_count = len(connection.queries)
        total_time = end_time - start_time

        print(
            f"Dashboard loaded in {total_time:.4f} seconds with {query_count} queries"
        )

        # Print slow queries
        slow_queries = [q for q in connection.queries if float(q["time"]) > 0.01]
        if slow_queries:
            print(f"\nSlow queries (>10ms):")
            for q in slow_queries[:5]:
                print(f"- {q['time']}s: {q['sql'][:100]}...")

        # Performance assertions
        self.assertLess(total_time, 1.0, "Dashboard response time too slow")
        self.assertLess(query_count, 20, "Too many database queries")

    @measure_time
    def test_contact_list_with_pagination(self):
        """Test contact list pagination performance"""
        self.client.login(username="optuser", password="optpass123")

        # Test different page sizes
        page_sizes = [10, 25, 50, 100]

        for page_size in page_sizes:
            reset_queries()

            start_time = time.time()
            response = self.client.get(
                reverse("contacts:person_list"), {"page_size": page_size}
            )
            end_time = time.time()

            self.assertEqual(response.status_code, 200)

            query_count = len(connection.queries)
            total_time = end_time - start_time

            print(f"Page size {page_size}: {total_time:.4f}s, {query_count} queries")

            # Pagination should not significantly affect query count
            self.assertLess(
                query_count, 15, f"Too many queries for page size {page_size}"
            )

    @override_settings(DEBUG=True)
    def test_n_plus_one_queries(self):
        """Detect and fix N+1 query problems"""
        self.client.login(username="optuser", password="optpass123")

        # Create more related data
        for i in range(10):
            contact = Contact.objects.create(
                type="person",
                first_name=f"N+1Test{i}",
                last_name="User",
                email=f"nplus{i}@example.com",
                user=self.user,
                office=self.office,
            )
            person = Person.objects.create(contact=contact)

            # Create multiple tasks per person
            for j in range(5):
                Task.objects.create(
                    title=f"Task {j} for N+1Test{i}",
                    due_date=timezone.now().date() + timedelta(days=j),
                    assigned_to=self.user,
                    created_by=self.user,
                    person=person,
                    status="pending",
                )

        # Test task list view for N+1 queries
        reset_queries()

        response = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(response.status_code, 200)

        # Analyze queries for N+1 patterns
        queries = connection.queries
        query_count = len(queries)

        # Group similar queries
        query_patterns = {}
        for q in queries:
            # Extract table name from query
            sql = q["sql"]
            if "FROM" in sql:
                table_match = sql.split("FROM")[1].split()[0].strip('"')
                if table_match not in query_patterns:
                    query_patterns[table_match] = 0
                query_patterns[table_match] += 1

        print(f"\nQuery patterns:")
        for table, count in query_patterns.items():
            print(f"- {table}: {count} queries")
            if count > 10:
                print(f"  WARNING: Possible N+1 query issue on {table}")

        # Assert no excessive queries
        self.assertLess(query_count, 50, "Possible N+1 query problem detected")

    @measure_time
    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }
    )
    def test_caching_effectiveness(self):
        """Test caching implementation effectiveness"""
        self.client.login(username="optuser", password="optpass123")

        # Clear cache
        cache.clear()

        # First request (cache miss)
        reset_queries()
        start_time = time.time()
        response1 = self.client.get(reverse("core:dashboard"))
        end_time = time.time()
        first_load_time = end_time - start_time
        first_query_count = len(connection.queries)

        print(
            f"First load (cache miss): {first_load_time:.4f}s, {first_query_count} queries"
        )

        # Second request (should use cache)
        reset_queries()
        start_time = time.time()
        response2 = self.client.get(reverse("core:dashboard"))
        end_time = time.time()
        cached_load_time = end_time - start_time
        cached_query_count = len(connection.queries)

        print(f"Cached load: {cached_load_time:.4f}s, {cached_query_count} queries")

        # Cache should improve performance
        self.assertLess(
            cached_load_time, first_load_time * 0.7, "Cache not effective enough"
        )
        self.assertLess(
            cached_query_count, first_query_count, "Cache should reduce queries"
        )

    def test_search_performance(self):
        """Test and optimize search functionality"""
        self.client.login(username="optuser", password="optpass123")

        search_terms = [
            "Test",  # Common term
            "Opt50",  # Specific term
            "nonexistent",  # No results
            "opt@",  # Email search
            "555",  # Phone search
        ]

        for term in search_terms:
            reset_queries()

            start_time = time.time()
            response = self.client.get(
                reverse("contacts:person_list"), {"search": term}
            )
            end_time = time.time()

            self.assertEqual(response.status_code, 200)

            search_time = end_time - start_time
            query_count = len(connection.queries)

            print(f"Search '{term}': {search_time:.4f}s, {query_count} queries")

            # Search should be fast
            self.assertLess(search_time, 0.5, f"Search for '{term}' too slow")

    def test_ajax_endpoint_performance(self):
        """Test AJAX endpoint response times"""
        self.client.login(username="optuser", password="optpass123")

        # Simulate AJAX requests
        ajax_endpoints = [
            ("tasks:task_list", {"format": "json"}),
            ("contacts:person_list", {"format": "json", "page_size": 10}),
            ("communications:communication_list", {"format": "json"}),
        ]

        for url_name, params in ajax_endpoints:
            reset_queries()

            start_time = time.time()
            response = self.client.get(
                reverse(url_name), params, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            )
            end_time = time.time()

            self.assertIn(response.status_code, [200, 201])

            ajax_time = end_time - start_time
            print(f"AJAX {url_name}: {ajax_time:.4f}s")

            # AJAX should be very fast
            self.assertLess(ajax_time, 0.3, f"AJAX endpoint {url_name} too slow")

    @profile_view
    def test_complex_view_profiling(self):
        """Profile complex view to identify bottlenecks"""
        self.client.login(username="optuser", password="optpass123")

        # Create complex data relationships
        church = Church.objects.create(
            contact=Contact.objects.create(
                type="church",
                church_name="Performance Church",
                email="perf@church.com",
                user=self.user,
                office=self.office,
            ),
            name="Performance Church",
            denomination="Test",
            congregation_size=1000,
        )

        # Add many members
        for i in range(50):
            contact = Contact.objects.create(
                type="person",
                first_name=f"Member{i}",
                last_name="Test",
                email=f"member{i}@church.com",
                user=self.user,
                office=self.office,
            )
            person = Person.objects.create(contact=contact, primary_church=church)

        # Profile church detail view
        response = self.client.get(
            reverse("churches:church_detail", args=[church.contact.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_bulk_operation_performance(self):
        """Test performance of bulk operations"""
        self.client.login(username="optuser", password="optpass123")

        # Create many items for bulk operations
        contact_ids = []
        for i in range(200):
            contact = Contact.objects.create(
                type="person",
                first_name=f"Bulk{i}",
                last_name="Test",
                email=f"bulk{i}@example.com",
                user=self.user,
                office=self.office,
            )
            contact_ids.append(contact.id)

        # Test bulk update
        start_time = time.time()

        # Simulate bulk update operation
        Contact.objects.filter(id__in=contact_ids[:100]).update(
            priority="high", updated_at=timezone.now()
        )

        end_time = time.time()
        bulk_update_time = end_time - start_time

        print(f"Bulk update of 100 records: {bulk_update_time:.4f}s")

        # Bulk operations should be efficient
        self.assertLess(bulk_update_time, 1.0, "Bulk update too slow")

    def test_database_connection_pooling(self):
        """Test database connection pooling effectiveness"""
        # Simulate multiple rapid requests
        request_times = []

        for i in range(10):
            self.client.login(username="optuser", password="optpass123")

            start_time = time.time()
            response = self.client.get(reverse("core:dashboard"))
            end_time = time.time()

            request_time = end_time - start_time
            request_times.append(request_time)

            self.assertEqual(response.status_code, 200)

            # Quick logout to simulate connection release
            self.client.logout()

        # Calculate average and check for consistency
        avg_time = sum(request_times) / len(request_times)
        max_time = max(request_times)
        min_time = min(request_times)

        print(
            f"Request times - Avg: {avg_time:.4f}s, Min: {min_time:.4f}s, Max: {max_time:.4f}s"
        )

        # Connection pooling should provide consistent performance
        variance = max_time - min_time
        self.assertLess(
            variance, 0.5, "High variance in request times - connection pooling issue?"
        )

    def test_static_file_serving_performance(self):
        """Test static file serving configuration"""
        # Note: In production, static files should be served by web server
        static_urls = [
            "/static/css/base.css",
            "/static/js/main.js",
            "/static/images/logo.png",
        ]

        for static_url in static_urls:
            start_time = time.time()
            response = self.client.get(static_url)
            end_time = time.time()

            load_time = end_time - start_time

            if response.status_code == 200:
                print(f"Static file {static_url}: {load_time:.4f}s")
                # Static files should load very quickly
                self.assertLess(
                    load_time, 0.1, f"Static file {static_url} loads too slowly"
                )
