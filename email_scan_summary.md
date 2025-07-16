# Email Scan Summary for Church Contacts

## Overview
Based on the investigation of the three churches from Issue #16 and Edith Parks, here are the contacts that need email scanning going back one year:

## Church Contacts

### 1. Grace City Church (Church ID: 753)
- **Church Email**: thiggins@thegracecity.com
- **Associated Person**: TJ Higgins (Person ID: 954)
  - Email: tjhiggins@thegracecity.com
  - Role: Associate Pastor
  - Current communications: 0

### 2. First Presbyterian (Church ID: 754)
- **Church Email**: None (Contact ID: 743)
- **Associated Person**: Edith Parks (Person ID: 955)
  - Email: reparks94@aol.com
  - Role: Committee Member
  - Current communications: 0

### 3. Greenville Christian Fellowship (Church ID: 779)
- **Church Email**: None
- **Associated Person**: Danny Mayfield (Person ID: 956)
  - Email: cactuscreek44@gmail.com
  - Role: Committee Member
  - Current communications: 0

## Additional Contact

### 4. Edith Parks (Additional Record)
- **Person ID**: 907
- **Email**: reparks94@aol.com
- **Phone**: (864) 630-2788
- **Current communications**: 1 (from April 2025)
- **Church associations**: None

## Email Addresses to Scan (1 Year Back)

1. **thiggins@thegracecity.com** (Grace City Church)
2. **tjhiggins@thegracecity.com** (TJ Higgins - Grace City Church)
3. **reparks94@aol.com** (Edith Parks - First Presbyterian)
4. **cactuscreek44@gmail.com** (Danny Mayfield - Greenville Christian Fellowship)

## Gmail Sync Command
To sync emails for these contacts going back one year, run:
```bash
python manage.py sync_gmail --days-back 365 --all-emails
```

## Notes
- Edith Parks has two Person records (IDs 907 and 955) with the same email address
- First Presbyterian church doesn't have a direct email address in the church contact
- The Gmail sync command will capture all emails and then associate them with the appropriate contacts
- Current email communications are minimal, suggesting that emails may not have been properly synced yet