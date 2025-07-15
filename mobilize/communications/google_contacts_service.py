import os
import json
from typing import Optional, List, Dict, Any, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from .models import Communication
from .gmail_service import GmailService

User = get_user_model()


class GoogleContactsService:
    """Google Contacts API service for contact synchronization"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/contacts.readonly',
        'https://www.googleapis.com/auth/contacts'
    ]
    
    def __init__(self, user):
        self.user = user
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Contacts API service with user credentials"""
        try:
            # Reuse Gmail service credentials since they should include contacts scope
            gmail_service = GmailService(self.user)
            credentials = gmail_service._get_user_credentials()
            
            if credentials and credentials.valid:
                self.service = build('people', 'v1', credentials=credentials)
            elif credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                gmail_service._save_user_credentials(credentials)
                self.service = build('people', 'v1', credentials=credentials)
        except Exception as e:
            print(f"Error initializing Google Contacts service: {e}")
            self.service = None
    
    def is_authenticated(self) -> bool:
        """Check if user has valid Google Contacts credentials"""
        return self.service is not None
    
    def get_all_contacts(self, page_size: int = 1000) -> List[Dict]:
        """Get all Google contacts for the user"""
        if not self.service:
            return []
        
        try:
            contacts = []
            next_page_token = None
            
            while True:
                request_params = {
                    'resourceName': 'people/me',
                    'pageSize': min(page_size, 1000),  # API max is 1000
                    'personFields': 'names,emailAddresses,phoneNumbers,addresses,organizations,birthdays,metadata'
                }
                
                if next_page_token:
                    request_params['pageToken'] = next_page_token
                
                results = self.service.people().connections().list(**request_params).execute()
                
                page_contacts = results.get('connections', [])
                contacts.extend(page_contacts)
                
                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    break
            
            return contacts
            
        except HttpError as error:
            print(f'Google Contacts API error: {error}')
            return []
    
    def parse_contact(self, contact_data: Dict) -> Dict:
        """Parse Google contact data into a standardized format"""
        parsed = {
            'google_resource_name': contact_data.get('resourceName', ''),
            'google_etag': contact_data.get('etag', ''),
            'first_name': '',
            'last_name': '',
            'full_name': '',
            'email': '',
            'phone': '',
            'organization': '',
            'title': '',
            'address': {},
            'created_at': None,
            'updated_at': None,
        }
        
        # Extract names
        names = contact_data.get('names', [])
        if names:
            name = names[0]  # Use primary name
            parsed['first_name'] = name.get('givenName', '')
            parsed['last_name'] = name.get('familyName', '')
            parsed['full_name'] = name.get('displayName', '')
        
        # Extract email (use primary email)
        emails = contact_data.get('emailAddresses', [])
        if emails:
            primary_email = next((e for e in emails if e.get('metadata', {}).get('primary')), emails[0])
            parsed['email'] = primary_email.get('value', '')
        
        # Extract phone (use primary phone)
        phones = contact_data.get('phoneNumbers', [])
        if phones:
            primary_phone = next((p for p in phones if p.get('metadata', {}).get('primary')), phones[0])
            parsed['phone'] = primary_phone.get('value', '')
        
        # Extract organization
        organizations = contact_data.get('organizations', [])
        if organizations:
            org = organizations[0]
            parsed['organization'] = org.get('name', '')
            parsed['title'] = org.get('title', '')
        
        # Extract address
        addresses = contact_data.get('addresses', [])
        if addresses:
            addr = addresses[0]
            parsed['address'] = {
                'street': addr.get('streetAddress', ''),
                'city': addr.get('city', ''),
                'state': addr.get('region', ''),
                'zip': addr.get('postalCode', ''),
                'country': addr.get('country', ''),
                'formatted': addr.get('formattedValue', '')
            }
        
        # Extract metadata dates
        metadata = contact_data.get('metadata', {})
        sources = metadata.get('sources', [])
        if sources:
            source = sources[0]
            parsed['created_at'] = source.get('updateTime')
            parsed['updated_at'] = source.get('updateTime')
        
        return parsed
    
    def sync_contacts_based_on_preference(self) -> Dict[str, Any]:
        """Sync contacts based on user's sync preference"""
        try:
            from mobilize.authentication.models import UserContactSyncSettings
            
            sync_settings = UserContactSyncSettings.objects.filter(user=self.user).first()
            if not sync_settings or sync_settings.sync_preference == 'disabled':
                return {'success': True, 'message': 'Contact sync is disabled', 'synced_count': 0}
            
            if sync_settings.sync_preference == 'crm_only':
                return self._sync_crm_contacts_only()
            elif sync_settings.sync_preference == 'all_contacts':
                return self._sync_all_contacts_to_crm()
            
        except Exception as e:
            error_msg = f"Contact sync failed: {str(e)}"
            print(error_msg)
            
            # Update sync settings with error
            try:
                sync_settings.update_last_sync(errors=[error_msg])
            except:
                pass
            
            return {'success': False, 'error': error_msg}
    
    def _sync_crm_contacts_only(self) -> Dict[str, Any]:
        """Sync only contacts that already exist in the CRM"""
        from mobilize.contacts.models import Contact, Person
        from mobilize.churches.models import Church
        
        google_contacts = self.get_all_contacts()
        synced_count = 0
        errors = []
        
        # Get all existing contacts with email addresses
        existing_contacts = Contact.objects.filter(email__isnull=False).exclude(email='')
        existing_emails = {contact.email.lower(): contact for contact in existing_contacts}
        
        for google_contact in google_contacts:
            try:
                parsed = self.parse_contact(google_contact)
                email = parsed.get('email', '').lower()
                
                if not email or email not in existing_emails:
                    continue
                
                # Update existing contact with Google data
                crm_contact = existing_emails[email]
                updated = self._update_contact_from_google(crm_contact, parsed)
                
                if updated:
                    synced_count += 1
                    
            except Exception as e:
                errors.append(f"Error syncing contact {parsed.get('email', 'unknown')}: {str(e)}")
        
        # Update sync settings
        try:
            from mobilize.authentication.models import UserContactSyncSettings
            sync_settings = UserContactSyncSettings.objects.get(user=self.user)
            sync_settings.update_last_sync(errors=errors if errors else None)
        except:
            pass
        
        return {
            'success': True,
            'synced_count': synced_count,
            'errors': errors,
            'message': f'Updated {synced_count} existing CRM contacts with Google data'
        }
    
    def _sync_all_contacts_to_crm(self) -> Dict[str, Any]:
        """Import all Google contacts into the CRM"""
        from mobilize.contacts.models import Contact, Person
        
        google_contacts = self.get_all_contacts()
        created_count = 0
        updated_count = 0
        errors = []
        
        for google_contact in google_contacts:
            try:
                parsed = self.parse_contact(google_contact)
                email = parsed.get('email', '').lower()
                
                if not email:
                    continue  # Skip contacts without email
                
                # Check if contact already exists
                existing_contact = Contact.objects.filter(email__iexact=email).first()
                
                if existing_contact:
                    # Update existing contact
                    updated = self._update_contact_from_google(existing_contact, parsed)
                    if updated:
                        updated_count += 1
                else:
                    # Create new contact
                    self._create_contact_from_google(parsed)
                    created_count += 1
                    
            except Exception as e:
                errors.append(f"Error importing contact {parsed.get('email', 'unknown')}: {str(e)}")
        
        # Update sync settings
        try:
            from mobilize.authentication.models import UserContactSyncSettings
            sync_settings = UserContactSyncSettings.objects.get(user=self.user)
            sync_settings.update_last_sync(errors=errors if errors else None)
        except:
            pass
        
        total_synced = created_count + updated_count
        return {
            'success': True,
            'synced_count': total_synced,
            'created_count': created_count,
            'updated_count': updated_count,
            'errors': errors,
            'message': f'Imported {created_count} new contacts and updated {updated_count} existing contacts'
        }
    
    def _update_contact_from_google(self, contact, google_data: Dict) -> bool:
        """Update existing CRM contact with Google data"""
        updated = False
        
        # Update fields if they're empty in CRM but have data in Google
        if not contact.first_name and google_data.get('first_name'):
            contact.first_name = google_data['first_name']
            updated = True
        
        if not contact.last_name and google_data.get('last_name'):
            contact.last_name = google_data['last_name']
            updated = True
        
        if not contact.phone and google_data.get('phone'):
            contact.phone = google_data['phone']
            updated = True
        
        # Update address fields if empty
        address_data = google_data.get('address', {})
        if address_data:
            if not contact.street_address and address_data.get('street'):
                contact.street_address = address_data['street']
                updated = True
            
            if not contact.city and address_data.get('city'):
                contact.city = address_data['city']
                updated = True
            
            if not contact.state and address_data.get('state'):
                contact.state = address_data['state']
                updated = True
            
            if not contact.zip_code and address_data.get('zip'):
                contact.zip_code = address_data['zip']
                updated = True
        
        # Update Google-specific fields
        if google_data.get('google_resource_name'):
            contact.google_resource_name = google_data['google_resource_name']
            updated = True
        
        if updated:
            contact.save()
        
        return updated
    
    def _create_contact_from_google(self, google_data: Dict):
        """Create new CRM contact from Google data"""
        from mobilize.contacts.models import Contact, Person
        
        # Create Contact first
        address_data = google_data.get('address', {})
        
        contact = Contact.objects.create(
            first_name=google_data.get('first_name', ''),
            last_name=google_data.get('last_name', ''),
            email=google_data.get('email', ''),
            phone=google_data.get('phone', ''),
            street_address=address_data.get('street', ''),
            city=address_data.get('city', ''),
            state=address_data.get('state', ''),
            zip_code=address_data.get('zip', ''),
            google_resource_name=google_data.get('google_resource_name', ''),
            type='person'  # Default to person type
        )
        
        # Create Person record
        person = Person.objects.create(
            contact=contact,
            occupation=google_data.get('title', ''),
            company=google_data.get('organization', '')
        )
        
        return contact

    def get_all_contacts_for_selection(self) -> List[Dict]:
        """Get all Google contacts formatted for selective import UI"""
        if not self.service:
            return []
        
        google_contacts = self.get_all_contacts()
        formatted_contacts = []
        
        for contact_data in google_contacts:
            parsed = self.parse_contact(contact_data)
            
            # Format contact for UI display
            formatted_contact = {
                'id': parsed['google_resource_name'],
                'name': parsed['full_name'] or f"{parsed['first_name']} {parsed['last_name']}".strip() or 'No Name',
                'email': parsed['email'],
                'organization': parsed['organization'],
                'first_name': parsed['first_name'],
                'last_name': parsed['last_name'],
                'phone': parsed['phone'],
                'title': parsed['title'],
                'address': parsed['address'],
                'google_data': parsed  # Keep original parsed data for import
            }
            
            # Only include contacts with either name or email
            if formatted_contact['name'] != 'No Name' or formatted_contact['email']:
                formatted_contacts.append(formatted_contact)
        
        # Sort by name
        formatted_contacts.sort(key=lambda x: x['name'].lower())
        
        return formatted_contacts

    def import_selected_contacts(self, selected_contact_ids: List[str]) -> Dict[str, Any]:
        """Import specific Google contacts by their resource names"""
        if not self.service or not selected_contact_ids:
            return {'success': False, 'error': 'No contacts selected or service unavailable'}
        
        try:
            # Get all contacts first (we could optimize this to fetch only selected ones)
            all_contacts = self.get_all_contacts_for_selection()
            
            # Filter to only selected contacts
            contacts_to_import = {contact['id']: contact for contact in all_contacts}
            selected_contacts = [contacts_to_import[contact_id] for contact_id in selected_contact_ids if contact_id in contacts_to_import]
            
            if not selected_contacts:
                return {'success': False, 'error': 'No valid contacts found to import'}
            
            imported_count = 0
            updated_count = 0
            errors = []
            
            print(f"Starting import of {len(selected_contacts)} selected contacts")
            
            for contact in selected_contacts:
                try:
                    print(f"Processing contact: {contact.get('name', 'Unknown')}")
                    google_data = contact['google_data']
                    email = google_data.get('email', '').lower()
                    print(f"Contact email: {email or 'No email'}")
                    
                    if not email:
                        errors.append(f"Skipped contact '{contact['name']}' - no email address")
                        print(f"Skipping contact without email: {contact['name']}")
                        continue
                    
                    # Check if contact already exists
                    from mobilize.contacts.models import Contact
                    existing_contact = Contact.objects.filter(email__iexact=email).first()
                    
                    if existing_contact:
                        # Update existing contact
                        updated = self._update_contact_from_google(existing_contact, google_data)
                        if updated:
                            updated_count += 1
                            print(f"Updated existing contact: {email}")
                        else:
                            print(f"No changes needed for existing contact: {email}")
                    else:
                        # Create new contact
                        self._create_contact_from_google_with_office(google_data)
                        imported_count += 1
                        print(f"Created new contact: {email}")
                        
                except Exception as e:
                    errors.append(f"Error importing '{contact['name']}': {str(e)}")
            
            total_imported = imported_count + updated_count
            message = f"Successfully imported {imported_count} new contacts"
            if updated_count > 0:
                message += f" and updated {updated_count} existing contacts"
            
            return {
                'success': True,
                'imported_count': total_imported,
                'created_count': imported_count,
                'updated_count': updated_count,
                'errors': errors,
                'message': message
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Import failed: {str(e)}"}

    def _create_contact_from_google_with_office(self, google_data: Dict):
        """Create new CRM contact from Google data with office assignment"""
        from mobilize.contacts.models import Contact, Person
        from mobilize.admin_panel.models import UserOffice
        
        # Get the user's office assignment
        user_office = UserOffice.objects.filter(user_id=str(self.user.id)).first()
        office = user_office.office if user_office else None
        
        # Create Contact first
        address_data = google_data.get('address', {})
        
        contact = Contact.objects.create(
            first_name=google_data.get('first_name', ''),
            last_name=google_data.get('last_name', ''),
            email=google_data.get('email', ''),
            phone=google_data.get('phone', ''),
            street_address=address_data.get('street', ''),
            city=address_data.get('city', ''),
            state=address_data.get('state', ''),
            zip_code=address_data.get('zip', ''),
            google_resource_name=google_data.get('google_resource_name', ''),
            type='person',  # Default to person type
            office=office  # Assign to user's office
        )
        
        # Create Person record
        person = Person.objects.create(
            contact=contact,
            occupation=google_data.get('title', ''),
            company=google_data.get('organization', '')
        )
        
        return contact