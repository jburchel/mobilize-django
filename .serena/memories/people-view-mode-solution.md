# People View Mode Fix - Solution Implementation

## Root Cause Identified
The `CustomAuthMiddleware` in `mobilize/authentication/middleware.py` creates an `AuthenticatedUser` class that hardcodes user roles:
- Only `j.burchel@crossoverglobal.net` gets `super_admin` role
- ALL other users get `standard_user` role (line 45)
- No users can get `office_admin` role through this system

## Fix Required
Update the middleware to properly retrieve user roles from the database instead of hardcoding them.

## Implementation Plan
1. Modify the `AuthenticatedUser` class in middleware to query the database for the actual user role
2. Add proper error handling for missing users
3. Test the fix to ensure View Mode toggle appears for office admins
4. Clean up any debug code added during investigation

## Code Location
File: `mobilize/authentication/middleware.py`
Lines: ~40-45 (role assignment logic)