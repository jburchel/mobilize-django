# Committing People Page View Mode Fix

## Files Modified
- `mobilize/authentication/middleware.py` - Fixed hardcoded role assignment

## Changes Made
- Updated CustomAuthMiddleware to query User model for actual roles instead of hardcoding
- Added error handling for missing users
- Proper staff/superuser flag assignment based on role

## Expected Result
Office admins should now see the View Mode toggle on the People page.