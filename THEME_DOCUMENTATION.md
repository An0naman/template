# 🎨 System Theme Documentation

## Overview
The System Theme feature provides comprehensive theming and dark mode support for the application. It allows users to customize the visual appearance of the main interface while preserving the distinct styling of maintenance modules.

## Features

### 🌙 Dark Mode
- Toggle between light and dark themes
- Affects main interface, entries, and content areas
- Maintains readability with appropriate color contrast

### 🎨 Color Themes
- **Default Blue**: Classic Bootstrap-inspired blue theme
- **Emerald Green**: Fresh, nature-inspired green palette
- **Purple**: Modern purple/violet color scheme
- **Amber**: Warm, golden amber theme

### 📝 Typography
- **Font Size Options**: Small (14px), Normal (16px), Large (18px), Extra Large (20px)
- **Live Preview**: See changes in real-time
- **Accessibility**: Improved readability options

### ♿ Accessibility
- **High Contrast Mode**: Enhanced contrast for better visibility
- **ARIA Labels**: Proper accessibility markup
- **Keyboard Navigation**: Full keyboard support

## Implementation

### Database Schema
Theme settings are stored in the `system_params` table:
```sql
CREATE TABLE system_params (
    param_name TEXT PRIMARY KEY,
    param_value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Theme parameters:
- `theme_color_scheme`: Color theme (default, emerald, purple, amber)
- `theme_dark_mode`: Dark mode enabled (true/false)
- `theme_font_size`: Base font size (small, normal, large, extra-large)
- `theme_high_contrast`: High contrast mode (true/false)

### API Endpoints

#### GET `/api/theme_settings`
Retrieve current theme settings.

**Response:**
```json
{
    "theme": "default",
    "dark_mode": false,
    "font_size": "normal",
    "high_contrast": false
}
```

#### POST `/api/theme_settings`
Update theme settings.

**Request:**
```json
{
    "theme": "purple",
    "dark_mode": true,
    "font_size": "large",
    "high_contrast": false
}
```

**Response:**
```json
{
    "success": true,
    "message": "Theme settings saved successfully"
}
```

### Frontend Integration

Theme CSS is automatically injected into templates via the context processor:

```html
<!-- Theme CSS -->
<style>
    {{ theme_css|safe }}
</style>
```

### CSS Variables
The theme system uses CSS custom properties:

```css
:root {
    --bs-primary: #8b5cf6;
    --theme-bg-body: #121212;
    --theme-bg-card: #2d2d2d;
    --theme-text: #ffffff;
    --theme-font-size: 18px;
    --theme-contrast: 1.5;
}
```

## Usage

### Accessing Theme Settings
1. Go to **Maintenance** → **System Configuration**
2. Click **System Theme**
3. Configure your preferred settings
4. Click **Save Theme Settings**

### For Developers

#### Adding Theme Support to New Templates
Add the theme CSS injection to your template's `<head>`:

```html
<!-- Theme CSS -->
<style>
    {{ theme_css|safe }}
</style>
```

#### Using Theme Variables in CSS
```css
.my-component {
    background-color: var(--theme-bg-card);
    color: var(--theme-text);
    font-size: var(--theme-font-size);
}
```

#### Excluding Elements from Theme
To prevent theme changes from affecting specific elements:

```css
.maintenance-module,
.maintenance-module * {
    filter: none !important;
}
```

## Migration

Run the migration script to set up theme settings:

```bash
python migrate_theme_settings.py
```

## Testing

Test the theme API:

```bash
chmod +x test_theme_api.sh
./test_theme_api.sh
```

## File Structure

```
app/
├── api/
│   └── theme_api.py          # Theme API endpoints
├── routes/
│   └── maintenance_routes.py # Theme settings page route
├── templates/
│   ├── manage_theme_settings.html # Theme configuration UI
│   ├── index.html            # Updated with theme support
│   └── entry_detail.html     # Updated with theme support
├── migrate_theme_settings.py # Database migration
└── test_theme_api.sh         # API testing script
```

## Notes

- **Scope**: Theme changes affect main interface only
- **Persistence**: Settings persist across sessions
- **Performance**: CSS is generated server-side for optimal performance
- **Fallbacks**: Default values are provided if settings are missing
- **Maintenance Modules**: Preserve their distinct color schemes (blue/orange/green/purple)

## Future Enhancements

- Custom color picker for advanced users
- Theme scheduling (auto dark mode at sunset)
- Additional font family options
- Import/export theme configurations
- Theme preview without saving
