# People View Mode - Middleware Authentication Issue

## Critical Finding
Looking at `mobilize/authentication/middleware.py`, there's a custom `AuthenticatedUser` class that's created for session-based authentication. 

**Key Issue**: The middleware hardcodes role assignment:
```python
# Set role based on email - j.burchel@crossoverglobal.net is super admin
if email == "j.burchel@crossoverglobal.net":
    self.role = "super_admin"
else:
    self.role = "standard_user"  # Default for other users
```

This means:
1. Only j.burchel@crossoverglobal.net gets `super_admin` role
2. ALL other users get `standard_user` role regardless of their actual role in the database
3. No users get `office_admin` role through this middleware

## Solution Options
1. **Fix the middleware** to properly retrieve user role from database
2. **Update role assignment logic** to handle office admins
3. **Ensure proper Django User authentication** instead of custom middleware

## Immediate Fix
The middleware should query the actual User model to get the real role instead of hardcoding.