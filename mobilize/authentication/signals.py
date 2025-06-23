from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import User


@receiver(post_save, sender=User)
def create_person_for_user(sender, instance, created, **kwargs):
    """
    Create a Person record when a User is created.
    
    This ensures every user in the system also exists as a trackable contact.
    """
    if created and not instance.person:
        # Import here to avoid circular imports
        from mobilize.contacts.models import Contact, Person
        from mobilize.admin_panel.models import Office
        
        # Get the first office or create a default one
        default_office = Office.objects.first()
        if not default_office:
            default_office = Office.objects.create(
                name="Default Office",
                code="DEFAULT",
                is_active=True
            )
        
        # Create Contact record first
        contact = Contact.objects.create(
            type='person',
            first_name=instance.first_name or '',
            last_name=instance.last_name or '',
            email=instance.email,
            office=default_office,
            user=instance,  # Set the user as the creator
            priority='medium',
            status='active'
        )
        
        # Create Person record linked to Contact
        person = Person.objects.create(
            contact=contact
        )
        
        # Link the User to the Person
        instance.person = person
        instance.save(update_fields=['person'])


@receiver(post_save, sender=User)
def update_person_from_user(sender, instance, created, **kwargs):
    """
    Update the Person record when User information changes.
    
    This keeps the user's contact information in sync.
    """
    if not created and instance.person:
        # Update contact information from user data
        contact = instance.person.contact
        
        # Update fields if they've changed
        updated_fields = []
        
        if contact.first_name != (instance.first_name or ''):
            contact.first_name = instance.first_name or ''
            updated_fields.append('first_name')
            
        if contact.last_name != (instance.last_name or ''):
            contact.last_name = instance.last_name or ''
            updated_fields.append('last_name')
            
        if contact.email != instance.email:
            contact.email = instance.email
            updated_fields.append('email')
        
        if updated_fields:
            contact.save(update_fields=updated_fields + ['updated_at'])