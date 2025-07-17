from django.db import models
from django.utils import timezone  # If needed for default values
from mobilize.contacts.models import Contact


class Church(models.Model):
    """
    Church model for storing church organization information.

    This model represents church organizations in the CRM system.
    Matches the 'churches' table in the Supabase database.
    It extends the Contact model via a OneToOneField.
    """

    # Explicitly define the primary key to ensure proper auto-increment behavior
    id = models.AutoField(primary_key=True)

    # Note: Using separate id field to match existing database schema
    # The database has both 'id' (primary key) and 'contact_id' (foreign key)
    contact = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        related_name="church_details",
        db_column="contact_id",
    )

    # Church-specific fields
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The official name of the church.",
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    denomination = models.CharField(max_length=100, blank=True, null=True)
    website = models.CharField(
        max_length=255, blank=True, null=True
    )  # Using CharField to match Supabase
    year_founded = models.IntegerField(blank=True, null=True)

    # Size Information
    congregation_size = models.IntegerField(blank=True, null=True)
    weekly_attendance = models.IntegerField(blank=True, null=True)

    # Fields from mobilize-prompt-django.md
    service_times = models.JSONField(
        blank=True, null=True, help_text="e.g., Sunday 9am, Wednesday 7pm"
    )
    # pastor_name, pastor_email, pastor_phone are covered by Senior Pastor section below for now
    facilities = models.JSONField(
        blank=True, null=True, help_text="Details about church facilities."
    )
    ministries = models.JSONField(
        blank=True, null=True, help_text="List or details of church ministries."
    )
    primary_language = models.CharField(max_length=50, blank=True, null=True)
    secondary_languages = models.JSONField(
        blank=True, null=True, help_text="Other languages used in services/ministries."
    )

    # Senior Pastor Information
    pastor_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of the senior pastor (replaces senior_pastor_name).",
    )
    senior_pastor_first_name = models.CharField(max_length=255, blank=True, null=True)
    senior_pastor_last_name = models.CharField(max_length=255, blank=True, null=True)
    pastor_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Phone number of the senior pastor (replaces senior_pastor_phone).",
    )
    pastor_email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Email of the senior pastor (replaces senior_pastor_email).",
    )

    # Missions Pastor Information
    missions_pastor_first_name = models.CharField(max_length=255, blank=True, null=True)
    missions_pastor_last_name = models.CharField(max_length=255, blank=True, null=True)
    mission_pastor_phone = models.CharField(
        max_length=255, blank=True, null=True
    )  # Match Supabase field name
    mission_pastor_email = models.CharField(
        max_length=255, blank=True, null=True
    )  # Match Supabase field name

    # Primary Contact Information
    primary_contact_first_name = models.CharField(max_length=255, blank=True, null=True)
    primary_contact_last_name = models.CharField(max_length=255, blank=True, null=True)
    primary_contact_phone = models.CharField(max_length=255, blank=True, null=True)
    primary_contact_email = models.CharField(max_length=255, blank=True, null=True)
    main_contact_id = models.IntegerField(blank=True, null=True)

    # Church-specific pipeline field (generic pipeline_stage is on Contact)
    church_pipeline = models.CharField(max_length=255, blank=True, null=True)

    # Integration flag
    virtuous = models.BooleanField(blank=True, null=True)

    # Church-specific fields
    info_given = models.TextField(blank=True, null=True)

    # Note: The following fields are now on Contact model:
    # - priority, status, pipeline_stage
    # - assigned_to (via user field)
    # - date_closed (via status)
    # - source, referred_by (can use custom_fields)
    # - reason_closed (can use notes)
    # - owner_id (via user field)
    # - office_id (via office field)

    class Meta:
        db_table = "churches"
        verbose_name = "Church"
        verbose_name_plural = "Churches"
        ordering = ["name"]  # Order by church name
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["church_pipeline"]),
            models.Index(fields=["denomination"]),
            models.Index(fields=["congregation_size"]),
        ]

    def __str__(self):
        return (
            self.name
            if self.name
            else self.contact.church_name or f"Church (Contact ID: {self.contact_id})"
        )

    @property
    def full_address(self):
        """Return the full address as a formatted string."""
        # Address fields are on the related Contact model
        return self.contact.full_address

    def get_absolute_url(self):
        """Return the URL to access a detail record for this church."""
        from django.urls import reverse

        return reverse("churches:church_detail", args=[str(self.pk)])

    def get_primary_contact(self):
        """Get the primary contact person for this church."""
        primary_membership = self.memberships.filter(
            is_primary_contact=True, status="active"
        ).first()
        return primary_membership.person if primary_membership else None

    def get_all_contacts(self):
        """Get all active contacts for this church."""
        return self.memberships.filter(status="active").select_related(
            "person__contact"
        )


class ChurchMembership(models.Model):
    """
    Relationship model between Church and Person.

    Handles roles, primary contact designation, and membership status.
    """

    ROLE_CHOICES = [
        ("senior_pastor", "Senior Pastor"),
        ("associate_pastor", "Associate Pastor"),
        ("youth_pastor", "Youth Pastor"),
        ("worship_pastor", "Worship Pastor"),
        ("missions_pastor", "Missions Pastor"),
        ("admin_pastor", "Administrative Pastor"),
        ("elder", "Elder"),
        ("deacon", "Deacon"),
        ("board_member", "Board Member"),
        ("secretary", "Secretary"),
        ("treasurer", "Treasurer"),
        ("member", "Member"),
        ("regular_attendee", "Regular Attendee"),
        ("volunteer", "Volunteer"),
        ("committee_member", "Committee Member"),
        ("ministry_leader", "Ministry Leader"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("former", "Former"),
    ]

    person = models.ForeignKey(
        "contacts.Person", on_delete=models.CASCADE, related_name="church_memberships"
    )
    church = models.ForeignKey(
        Church, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default="member",
        help_text="The person's role in this church",
    )
    is_primary_contact = models.BooleanField(
        default=False, help_text="Is this person the primary contact for the church?"
    )
    start_date = models.DateField(
        default=timezone.now, help_text="When this relationship started"
    )
    end_date = models.DateField(
        null=True, blank=True, help_text="When this relationship ended (if applicable)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this membership/relationship",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "church_memberships"
        unique_together = ("person", "church")  # One relationship per person per church
        indexes = [
            models.Index(fields=["church"]),
            models.Index(fields=["person"]),
            models.Index(fields=["is_primary_contact"]),
            models.Index(fields=["status"]),
            models.Index(fields=["role"]),
        ]
        ordering = ["-is_primary_contact", "role", "person__contact__last_name"]

    def __str__(self):
        return f"{self.person.name} - {self.church.name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        """Override save to ensure only one primary contact per church."""
        if self.is_primary_contact:
            # Set all other memberships for this church as non-primary
            ChurchMembership.objects.filter(
                church=self.church, is_primary_contact=True
            ).exclude(pk=self.pk).update(is_primary_contact=False)
        super().save(*args, **kwargs)

    @property
    def is_pastor(self):
        """Check if this membership represents a pastoral role."""
        pastoral_roles = [
            "senior_pastor",
            "associate_pastor",
            "youth_pastor",
            "worship_pastor",
            "missions_pastor",
            "admin_pastor",
        ]
        return self.role in pastoral_roles

    @property
    def is_leadership(self):
        """Check if this membership represents a leadership role."""
        leadership_roles = [
            "senior_pastor",
            "associate_pastor",
            "youth_pastor",
            "worship_pastor",
            "missions_pastor",
            "admin_pastor",
            "elder",
            "deacon",
            "board_member",
            "ministry_leader",
        ]
        return self.role in leadership_roles
