# Test Communications Guide

This guide explains how to use the `create_test_communications` management command to create test data for verifying the "View All" button functionality on person detail pages.

## Problem Statement

The issue report states: "The View All button on the person detail pages Recent Communications card I think is only showing all email and not all communications."

## Management Command Usage

### Basic Usage

```bash
# Create test communications for a specific person by ID
python manage.py create_test_communications --person-id 123

# Create test communications for a person by name
python manage.py create_test_communications --person-name "John Doe"

# Create test communications for the first person found (fallback)
python manage.py create_test_communications
```

### Advanced Options

```bash
# Dry run to see what would be created without actually creating records
python manage.py create_test_communications --person-id 123 --dry-run

# Create more communications per type (default is 2)
python manage.py create_test_communications --person-id 123 --count 3

# Clean up all test communications created by this command
python manage.py create_test_communications --cleanup
```

## What the Command Creates

The command creates test communications for all communication types defined in the `Communication.TYPE_CHOICES`:

1. **Email** - Test emails with subjects like "Test Email: Meeting Request"
2. **Phone Call** - Call records with discussion summaries
3. **Text Message** - Short text message communications
4. **Meeting** - In-person meeting records
5. **Video Call** - Video conference session records

### Data Created per Communication Type

- **Subject**: Type-specific meaningful subjects
- **Message**: Brief description/summary
- **Content**: Detailed content appropriate for the communication type
- **Direction**: Random selection of 'inbound' or 'outbound'
- **Date**: Random dates within the past 30 days
- **Status**: Set to 'sent' for completed communications
- **External ID**: Unique identifier for easy cleanup (format: `test-communication-{type}-{index}`)

## Testing the "View All" Button

1. **Run the command** to create test data for a specific person:
   ```bash
   python manage.py create_test_communications --person-id 123
   ```

2. **Navigate to the person detail page** in your browser:
   ```
   http://localhost:8000/contacts/person/123/
   ```

3. **Locate the "Recent Communications" card** on the person detail page

4. **Click the "View All" button** to see if it displays all communication types or only emails

5. **Verify the results**:
   - The "View All" page should show all 5 communication types
   - Check if all types are displayed: Email, Phone Call, Text Message, Meeting, Video Call
   - Verify that the dates, subjects, and content are displayed correctly

## Expected Behavior

The "View All" button should display all communication types associated with the person, not just emails. If it only shows emails, this confirms the bug reported.

## Cleanup

After testing, clean up the test data:

```bash
python manage.py create_test_communications --cleanup
```

This will remove all test communications created by this command (identified by the `external_id` field starting with "test-communication-").

## Command Output Example

```
python manage.py create_test_communications --person-id 123

Created Email communication: Test Email: Meeting Request - John Doe
Created Email communication: Test Email: Meeting Request - John Doe
Created Phone Call communication: Phone Call: Follow-up Discussion
Created Phone Call communication: Phone Call: Follow-up Discussion
Created Text Message communication: Text: Event Reminder
Created Text Message communication: Text: Event Reminder
Created Meeting communication: Meeting: Initial Consultation
Created Meeting communication: Meeting: Initial Consultation
Created Video Call communication: Video Call: Missions Training Session
Created Video Call communication: Video Call: Missions Training Session

Successfully created 10 test communications for John Doe

Summary:
Person: John Doe
Contact ID: 123
Office: Main Office
Communications created: 10

Test the "View All" button at the person detail page to verify it shows all communication types.
```

## Technical Notes

- The command requires the person to have an office assigned
- Communications are created with realistic, type-appropriate content
- All communications are marked with a test identifier for easy cleanup
- The command handles both Person ID and name-based lookups
- Dry run mode allows you to preview what would be created without making changes

## Troubleshooting

- **"Person not found"**: Verify the person ID exists or try searching by name
- **"No user found"**: Ensure at least one user exists in the system
- **"Person must have an office assigned"**: The person needs to be associated with an office

This command provides a comprehensive way to test the "View All" button functionality with diverse communication types.