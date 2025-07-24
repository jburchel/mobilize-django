# People View Mode Analysis - Root Cause Found

## Code Flow Analysis

1. **User Model**: Has `role` field with choices: `super_admin`, `office_admin`, `standard_user`, `limited_user`
2. **DataAccessManager**: 
   - `__init__`: Sets `self.user_role = getattr(user, "role", "standard_user")`
   - `can_view_all_data()`: Returns `self.user_role in ["super_admin", "office_admin"]`
3. **Person List View**: Sets context `"can_toggle_view": access_manager.can_view_all_data()`
4. **Template**: Conditionally shows toggle with `{% if can_toggle_view %}`

## Issue Analysis
The logic appears correct, so the problem is likely:
- User role is not `super_admin` or `office_admin` 
- User object doesn't have `role` attribute (defaults to `standard_user`)
- Some middleware or authentication issue affecting user object

## Next Steps
1. Debug the actual user role value being set
2. Check how users are being authenticated/created
3. Verify the role assignment process
4. Test with a known admin user