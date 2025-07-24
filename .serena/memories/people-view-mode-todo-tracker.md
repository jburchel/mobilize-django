# People View Mode TODO Tracker

This tracks the implementation steps to fix the missing View Mode toggle on the People page.

## Root Cause Found
The `CustomAuthMiddleware` hardcodes user roles - only j.burchel@crossoverglobal.net gets super_admin, everyone else gets standard_user. This prevents office_admin users from seeing the View Mode toggle.

## Fix Required
Update middleware to query the User model for actual roles instead of hardcoding them.