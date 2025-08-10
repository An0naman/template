# Section Styling Feature - Quick Start Guide

## Overview
The Section Styling feature allows you to customize the visual appearance of content sections, filter areas, and entry cards throughout your application. This includes border styles, spacing, and background effects.

## Features Added

### 🎨 Border Styles
- **Rounded** (Default): Standard rounded corners (0.75rem radius)
- **Sharp**: No border radius for a modern, angular look  
- **Subtle**: Slightly rounded corners (0.375rem radius)
- **Bold**: Pronounced rounded corners (1.25rem radius)

### 📏 Section Spacing
- **Compact**: Reduced padding and margins (1rem)
- **Normal** (Default): Standard spacing (1.5rem)
- **Spacious**: Increased spacing for better readability (2rem)

### ✨ Background Effects
- **Flat**: No shadows, seamless blend with page background
- **Subtle** (Default): Light shadow and clear borders
- **Elevated**: Strong shadows for a floating card effect
- **Glassmorphic**: Semi-transparent background with blur effects

## How to Use

1. **Access Settings**: Go to Settings → System Configuration → System Theme
2. **Find Section Styling**: Scroll down to the "Section Styling" section
3. **Choose Options**: Select your preferred border style, spacing, and background effect
4. **Preview**: Use the live preview to see how your choices look
5. **Save**: Click "Save Theme Settings" to apply changes

## Technical Details

### Database Changes
- Added `theme_section_styles` parameter to SystemParameters table
- Stores JSON with `border_style`, `spacing`, and `background` values

### API Updates
- GET `/api/theme_settings` now returns `section_styles` object
- POST `/api/theme_settings` accepts `section_styles` in request body

### CSS Implementation
- New CSS variables for section styling
- Applied to `.content-section`, `.filter-section`, and `.entry-item` classes
- Supports both light and dark mode variations

## Migration

If you're upgrading from a previous version:

```bash
# Run the migration script
python3 migrate_section_styles.py
```

This will add the section styling parameters to your existing database.

## Testing

Test the API functionality:

```bash
# Make the test script executable and run it
chmod +x test_section_styles_api.sh
./test_section_styles_api.sh
```

## Files Modified

- `app/api/theme_api.py` - Added section styling support to API
- `app/templates/manage_theme_settings.html` - Added UI controls and JavaScript
- `THEME_DOCUMENTATION.md` - Updated documentation
- `migrate_section_styles.py` - Migration script for existing installations
- `test_section_styles_api.sh` - API testing script

## Examples

### API Request Example
```json
{
  "theme": "purple",
  "dark_mode": false,
  "section_styles": {
    "border_style": "bold",
    "spacing": "spacious", 
    "background": "elevated"
  }
}
```

### CSS Variables Generated
```css
:root {
  --section-border-radius: 1.25rem;
  --section-padding: 2rem;
  --section-margin-bottom: 2rem;
  --section-bg: #fdfdfd;
  --section-border: #c1c8cd;
  --section-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

The feature is fully backward compatible - existing installations without section styles will use the default "subtle" appearance.
