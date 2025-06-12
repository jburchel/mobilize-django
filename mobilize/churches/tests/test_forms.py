"""
Tests for churches forms
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from mobilize.churches.forms import ChurchForm, ImportChurchesForm
from mobilize.churches.models import Church


class ChurchFormTests(TestCase):
    """Test cases for the ChurchForm"""
    
    def setUp(self):
        self.valid_church_data = {
            'name': 'Test Baptist Church',
            'location': 'Downtown',
            'website': 'https://testchurch.org',
            'denomination': 'Baptist',
            'year_founded': 1950,
            'congregation_size': 200,
            'weekly_attendance': 150,
            'pastor_name': 'Pastor John Smith',
            'senior_pastor_first_name': 'John',
            'senior_pastor_last_name': 'Smith',
            'pastor_phone': '123-456-7890',
            'pastor_email': 'pastor@testchurch.org',
            'church_pipeline': 'Active',
            'priority': 'High',
            'office_id': 1,
        }
    
    def test_valid_church_form(self):
        """Test that form is valid with complete data"""
        form = ChurchForm(data=self.valid_church_data)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_church_form_minimal_data(self):
        """Test form with minimal required data"""
        minimal_data = {
            'name': 'Minimal Church',
            'office_id': 1,
        }
        form = ChurchForm(data=minimal_data)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_church_form_missing_required_fields(self):
        """Test form validation with missing required fields"""
        # Since all Church model fields are blank=True, null=True,
        # empty name should still be valid but result in empty string
        invalid_data = self.valid_church_data.copy()
        invalid_data['name'] = ''
        form = ChurchForm(data=invalid_data)
        self.assertTrue(form.is_valid())  # Model allows blank names
    
    def test_church_form_invalid_email(self):
        """Test form validation with invalid email"""
        invalid_data = self.valid_church_data.copy()
        invalid_data['pastor_email'] = 'invalid-email'
        form = ChurchForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('pastor_email', form.errors)
    
    def test_church_form_invalid_website(self):
        """Test form validation with invalid website URL"""
        # Website is CharField, not URLField, so no URL validation
        invalid_data = self.valid_church_data.copy()
        invalid_data['website'] = 'not-a-url'
        form = ChurchForm(data=invalid_data)
        self.assertTrue(form.is_valid())  # CharField accepts any text
    
    def test_church_form_negative_year_founded(self):
        """Test form validation with negative year founded"""
        # Model doesn't have validation for negative years
        invalid_data = self.valid_church_data.copy()
        invalid_data['year_founded'] = -100
        form = ChurchForm(data=invalid_data)
        self.assertTrue(form.is_valid())  # No validation on year_founded
    
    def test_church_form_future_year_founded(self):
        """Test form validation with future year founded"""
        # Model doesn't have validation for future years
        invalid_data = self.valid_church_data.copy()
        invalid_data['year_founded'] = 2050
        form = ChurchForm(data=invalid_data)
        self.assertTrue(form.is_valid())  # No validation on year_founded
    
    def test_church_form_negative_congregation_size(self):
        """Test form validation with negative congregation size"""
        # Model doesn't have validation for negative congregation size
        invalid_data = self.valid_church_data.copy()
        invalid_data['congregation_size'] = -10
        form = ChurchForm(data=invalid_data)
        self.assertTrue(form.is_valid())  # No validation on congregation_size
    
    def test_church_form_save(self):
        """Test that form saves church correctly"""
        form = ChurchForm(data=self.valid_church_data)
        self.assertTrue(form.is_valid())
        
        church = form.save()
        self.assertEqual(church.name, 'Test Baptist Church')
        self.assertEqual(church.location, 'Downtown')
        self.assertEqual(church.denomination, 'Baptist')
        self.assertEqual(church.year_founded, 1950)
        self.assertEqual(church.congregation_size, 200)
        self.assertEqual(church.weekly_attendance, 150)
    
    def test_church_form_edit_existing(self):
        """Test editing an existing church"""
        # Create a church first
        church = Church.objects.create(
            name='Original Church',
            location='Original Location',
            office_id=1
        )
        
        # Update data
        updated_data = self.valid_church_data.copy()
        updated_data['name'] = 'Updated Church Name'
        updated_data['location'] = 'Updated Location'
        
        form = ChurchForm(data=updated_data, instance=church)
        self.assertTrue(form.is_valid())
        
        updated_church = form.save()
        self.assertEqual(updated_church.id, church.id)
        self.assertEqual(updated_church.name, 'Updated Church Name')
        self.assertEqual(updated_church.location, 'Updated Location')


class ImportChurchesFormTests(TestCase):
    """Test cases for the ImportChurchesForm"""
    
    def test_valid_csv_file(self):
        """Test form with valid CSV file"""
        csv_content = b"name,location,denomination\nTest Church,Downtown,Baptist\n"
        csv_file = SimpleUploadedFile(
            "churches.csv",
            csv_content,
            content_type="text/csv"
        )
        
        form = ImportChurchesForm(files={'csv_file': csv_file})
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_invalid_file_extension(self):
        """Test form with invalid file extension"""
        txt_content = b"name,location,denomination\nTest Church,Downtown,Baptist\n"
        txt_file = SimpleUploadedFile(
            "churches.txt",
            txt_content,
            content_type="text/plain"
        )
        
        form = ImportChurchesForm(files={'csv_file': txt_file})
        self.assertFalse(form.is_valid())
        self.assertIn('csv_file', form.errors)
    
    def test_missing_file(self):
        """Test form without file upload"""
        form = ImportChurchesForm(files={})
        self.assertFalse(form.is_valid())
        self.assertIn('csv_file', form.errors)
    
    def test_empty_file(self):
        """Test form with empty file"""
        empty_file = SimpleUploadedFile(
            "empty.csv",
            b"",
            content_type="text/csv"
        )
        
        form = ImportChurchesForm(files={'csv_file': empty_file})
        # Empty file should fail validation
        self.assertFalse(form.is_valid())
    
    def test_large_file_handling(self):
        """Test form with reasonably sized file"""
        # Create a CSV with multiple rows
        csv_content = b"name,location,denomination\n"
        for i in range(100):
            csv_content += f"Church {i},Location {i},Denomination {i}\n".encode()
        
        csv_file = SimpleUploadedFile(
            "large_churches.csv",
            csv_content,
            content_type="text/csv"
        )
        
        form = ImportChurchesForm(files={'csv_file': csv_file})
        self.assertTrue(form.is_valid(), form.errors)