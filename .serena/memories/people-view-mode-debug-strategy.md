# People View Mode Debug Strategy

## Debugging Steps to Identify Issue

### 1. Add Debug Output to Template
Add debug information to show actual values in the lazy template:
- `user.role` value
- `can_toggle_view` value  
- `user_role` value from context
- User authentication status

### 2. Check User Authentication System
The middleware shows a custom `AuthenticatedUser` class that might not have proper role assignment.

### 3. Investigate Role Assignment
Look at how users get their roles assigned, especially in the authentication process.

### 4. Test with Known Data
Need to verify what the actual user object looks like when the view is accessed.

## Likely Root Cause
Based on the middleware code, it looks like there's a custom authentication system that creates an `AuthenticatedUser` object with role assignment logic. This might be overriding the Django User model's role field.