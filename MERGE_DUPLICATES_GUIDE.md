# Merge Duplicates Feature Guide

## Overview

The merge duplicates feature helps you clean up duplicate contacts in your CRM system. It provides both automatic cleanup and manual merge capabilities.

## What Was Already Done

### ✅ Automatic Email Duplicate Cleanup
- **Cleaned up 10 email duplicates** automatically
- Kept the oldest contact (lowest ID) and deleted newer duplicates
- One contact couldn't be deleted due to foreign key constraints (Peggy Summers - referenced by a church)

### 📊 Current Duplicate Status
- **Email duplicates**: 1 remaining (foreign key constraint)
- **Name duplicates**: 59 (people with same first+last name)
- **Church duplicates**: 45 (churches with same name)

## Available Commands

### 1. Simple Duplicate Cleanup (Recommended)
```bash
# Preview what would be cleaned up
python manage.py simple_duplicate_cleanup --dry-run

# Actually clean up email duplicates
python manage.py simple_duplicate_cleanup
```

**What it does:**
- Finds contacts with identical emails
- Keeps the oldest contact (lowest ID)
- Deletes newer duplicates
- Safe and reliable

### 2. Advanced Merge Duplicates (Use with caution)
```bash
# Preview all duplicates
python manage.py merge_duplicates --dry-run

# Auto-merge obvious duplicates
python manage.py merge_duplicates --auto-merge

# Manually merge specific contacts
python manage.py merge_duplicates --merge-contact-ids="123,456,789" --keep-contact-id=123
```

**What it does:**
- Detects email, name, and church name duplicates
- Can merge data from duplicates into the primary contact
- More complex but may trigger database constraint issues

## Manual Merge Examples

### Merge Specific People
If you find people with the same name but different emails, you can manually merge them:

```bash
# Example: Merge contacts 566 and 819, keeping 566
python manage.py merge_duplicates --merge-contact-ids="566,819" --keep-contact-id=566
```

### Merge Specific Churches
```bash
# Example: Merge church contacts 200 and 300, keeping 200  
python manage.py merge_duplicates --merge-contact-ids="200,300" --keep-contact-id=200
```

## How to Find Duplicates

### Check Email Duplicates
```python
from mobilize.contacts.models import Contact
from django.db.models import Count

email_dups = Contact.objects.values('email').annotate(
    count=Count('id')
).filter(count__gt=1, email__isnull=False).exclude(email='')

for dup in email_dups:
    email = dup['email']
    contacts = Contact.objects.filter(email=email)
    print(f"Email {email}: {[(c.id, str(c)) for c in contacts]}")
```

### Check Name Duplicates
```python
name_dups = Contact.objects.filter(type='person').values(
    'first_name', 'last_name'
).annotate(count=Count('id')).filter(
    count__gt=1, 
    first_name__isnull=False, 
    last_name__isnull=False
).exclude(first_name='').exclude(last_name='')

for dup in name_dups[:5]:  # Show first 5
    first, last = dup['first_name'], dup['last_name']
    contacts = Contact.objects.filter(
        type='person', 
        first_name=first, 
        last_name=last
    )
    print(f"Name {first} {last}: {[(c.id, c.email) for c in contacts]}")
```

## Best Practices

### 1. Always Use Dry Run First
```bash
python manage.py simple_duplicate_cleanup --dry-run
```

### 2. Start with Email Duplicates
- Email duplicates are the most reliable indicator of true duplicates
- The simple cleanup command handles these safely

### 3. Manual Review for Name/Church Duplicates
- People with same names might be different people
- Churches with same names might be in different locations
- Review manually before merging

### 4. Check Foreign Key Constraints
Some contacts can't be deleted because they're referenced by other records:
- Church main contacts
- Task assignees
- Communication recipients

## Troubleshooting

### Foreign Key Constraint Errors
If you get errors like "violates foreign key constraint", it means the contact is referenced elsewhere:
1. Find what's referencing it
2. Update the references first
3. Then delete the duplicate

### Database Trigger Issues
The database has triggers that sync names between tables. If you get trigger errors:
1. Use the simple cleanup command instead
2. Or contact your database administrator

### Failed Merges
If the advanced merge fails:
1. Use the simple cleanup for email duplicates
2. Manually review and merge name/church duplicates one by one

## Next Steps

1. **Run the simple cleanup periodically** to catch new email duplicates
2. **Review name duplicates manually** - many might be legitimate different people
3. **Review church duplicates** - many might be different locations or denominations
4. **Consider adding duplicate prevention** to your contact creation process

## Example Workflow

```bash
# 1. See what duplicates exist
python manage.py merge_duplicates --dry-run

# 2. Clean up obvious email duplicates
python manage.py simple_duplicate_cleanup

# 3. Manually review and merge specific cases
python manage.py merge_duplicates --merge-contact-ids="123,456" --keep-contact-id=123

# 4. Verify results
python manage.py merge_duplicates --dry-run
```