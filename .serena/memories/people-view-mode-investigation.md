# People Page View Mode Investigation

## Problem
The People page View Mode toggle is not appearing. It should allow admins to switch between:
1. "View All Offices" (for Super Admins) / "My Office" (for Office Admins) 
2. "My People Only"

## Current Template Structure (person_list.html)
- View Mode section is wrapped in `{% if can_toggle_view %}`
- Has debug comment showing: `can_toggle_view={{ can_toggle_view }}, user_role={{ user_role }}`
- Template structure looks correct for both super_admin and regular admin users
- Contains proper buttons and logic for the toggle functionality

## Next Steps
Need to investigate the view that renders this template to check:
1. How `can_toggle_view` variable is being set
2. How `user_role` is being determined
3. Whether the view logic handles the view_mode parameter correctly