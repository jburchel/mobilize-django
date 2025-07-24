# People View Mode Investigation TODO

## Steps to investigate and fix the missing View Mode toggle:

1. ✅ Confirmed People page template structure is correct
2. ✅ Confirmed view passes correct context variables 
3. 🔄 Need to investigate DataAccessManager.can_view_all_data() method
4. ⏳ Check user role/permission logic 
5. ⏳ Test the fix and verify functionality works
6. ⏳ Clean up any debug code if needed

## Key Findings:
- People page defaults to `person_list_lazy.html` template
- Template has proper View Mode toggle structure for both super_admin and office_admin
- Toggle visibility controlled by `can_toggle_view = access_manager.can_view_all_data()`
- Need to investigate why can_view_all_data() returns False