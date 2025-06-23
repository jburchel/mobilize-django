# Logo Files for Mobilize CRM

Please add your logo files to this directory:

## Required Files:

### 1. favicon.png
- **Size**: 32x32 pixels or 16x16 pixels
- **Format**: PNG (preferred) or ICO
- **Purpose**: Browser tab icon
- **Note**: Should be a square version of your logo that's recognizable at small sizes

### 2. logo.png
- **Size**: 32x32 pixels (or similar small size)
- **Format**: PNG with transparent background
- **Purpose**: Sidebar logo next to "Mobilize CRM" text
- **Note**: Should work well on the dark gradient background (consider white/light version)

## Tips:
- For the favicon, make sure it's recognizable even at 16x16 pixels
- For the sidebar logo, ensure it has good contrast against the dark blue/green gradient
- PNG format with transparency is recommended for both
- Consider having a white or light-colored version for the sidebar since it sits on a dark background

## Current Implementation:
- Favicon: Referenced in `<head>` section as `{% static 'images/favicon.png' %}`
- Sidebar logo: Referenced next to "Mobilize CRM" text as `{% static 'images/logo.png' %}`