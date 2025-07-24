# People View Mode - Final Implementation Plan

## Steps to Fix the Issue

### 1. Update Middleware Role Assignment
- Fix the hardcoded role assignment in `CustomAuthMiddleware` 
- Query the User model to get the actual user role from database
- Ensure office_admin users can get their proper role

### 2. Test the Fix
- Verify View Mode toggle appears for office_admin users
- Confirm super_admin functionality still works
- Test that standard_user doesn't see the toggle

### 3. Clean Up
- Remove any debug code added during investigation
- Update any related documentation if needed

## Files to Modify
- `mobilize/authentication/middleware.py` (primary fix)
- Possibly add debug output temporarily to verify fix works

## Expected Result
Office admins should see the View Mode toggle with options to switch between "My Office" and "My People Only".