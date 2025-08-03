# 🎨 System Theme Documentation

A comprehensive guide to the Template Flask application's dynamic theme system with dark mode support and customizable color schemes.

## 📋 **Table of Contents**

- [Overview](#overview)
- [Features](#features)
- [Installation & Setup](#installation--setup)
- [Theme Configuration](#theme-configuration)
- [Color Schemes](#color-schemes)
- [Implementation Details](#implementation-details)
- [API Reference](#api-reference)
- [Frontend Integration](#frontend-integration)
- [Customization Guide](#customization-guide)
- [Troubleshooting](#troubleshooting)

---

## 🌟 **Overview**

The System Theme feature provides comprehensive theming and dark mode support for the application. It allows users to customize the visual appearance of the main interface while preserving the distinct styling of maintenance modules.

### **Key Benefits**
- 🎯 **User-Centric**: Personalized visual experience
- ♿ **Accessible**: High contrast and typography options
- 🌙 **Modern**: Native dark mode support
- 🔄 **Dynamic**: Real-time theme switching
- 📱 **Responsive**: Consistent across all devices

---

## 🌟 **Features**

### **🌙 Dark Mode**
- **Toggle Functionality**: Seamless light/dark theme switching
- **Bootstrap Integration**: Native Bootstrap 5.3.3 dark mode support
- **Content Preservation**: Maintains readability with appropriate color contrast
- **System Integration**: Respects user's system theme preferences

### **🎨 Color Themes**
| Theme | Primary Color | Secondary Color | Use Case |
|-------|---------------|-----------------|----------|
| **Default Blue** | `#0d6efd` | `#6f42c1` | Classic Bootstrap-inspired theme |
| **Emerald Green** | `#10b981` | `#059669` | Fresh, nature-inspired palette |
| **Purple** | `#8b5cf6` | `#7c3aed` | Modern purple/violet scheme |
| **Amber** | `#f59e0b` | `#d97706` | Warm, golden amber theme |

### **📝 Typography Options**
| Size | Base Font | Line Height | Use Case |
|------|-----------|-------------|----------|
| **Small** | 14px | 1.4 | Compact layouts |
| **Normal** | 16px | 1.5 | Default setting |
| **Large** | 18px | 1.6 | Better readability |
| **Extra Large** | 20px | 1.7 | Accessibility needs |

### **♿ Accessibility Features**
- **High Contrast Mode**: Enhanced contrast ratios for better visibility
- **ARIA Labels**: Proper accessibility markup throughout
- **Keyboard Navigation**: Full keyboard support for theme controls
- **Screen Reader Support**: Compatible with assistive technologies
- **Focus Indicators**: Clear focus states for interactive elements

---

## 🚀 **Installation & Setup**

### **Prerequisites**
The theme system is built into the application core. No additional installation required.

### **Initial Configuration**
1. **Access Theme Settings**:
   - Navigate to Settings → System Configuration → System Theme
   - Or directly access via URL: `/maintenance/theme_settings`

2. **First-Time Setup**:
   ```python
   # Default theme parameters are automatically initialized
   {
       "theme_color_scheme": "default",
       "theme_dark_mode": False,
       "theme_font_size": "normal", 
       "theme_high_contrast": False
   }
   ```

3. **Verify Installation**:
   ```bash
   # Check if theme CSS is being generated
   curl http://localhost:5000/api/theme_settings
   ```

---

## ⚙️ **Theme Configuration**

### **Available Settings**

#### **Color Scheme Options**
```python
THEME_COLOR_SCHEMES = {
    'default': {
        'primary': '#0d6efd',
        'secondary': '#6f42c1',
        'name': 'Default Blue'
    },
    'emerald': {
        'primary': '#10b981',
        'secondary': '#059669', 
        'name': 'Emerald Green'
    },
    'purple': {
        'primary': '#8b5cf6',
        'secondary': '#7c3aed',
        'name': 'Purple'
    },
    'amber': {
        'primary': '#f59e0b',
        'secondary': '#d97706',
        'name': 'Amber'
    }
}
```

#### **Font Size Mapping**
```python
FONT_SIZE_MAP = {
    'small': '14px',
    'normal': '16px', 
    'large': '18px',
    'extra-large': '20px'
}
```

#### **Configuration via Web Interface**
1. **Theme Selection**: Choose from 4 pre-built color schemes
2. **Dark Mode Toggle**: Enable/disable dark mode
3. **Font Size**: Select from 4 typography options
4. **High Contrast**: Toggle high contrast mode
5. **Live Preview**: See changes instantly

#### **Configuration via API**
```bash
# Update theme settings
curl -X POST http://localhost:5000/api/theme_settings \
  -H "Content-Type: application/json" \
  -d '{
    "theme_color_scheme": "purple",
    "theme_dark_mode": true,
    "theme_font_size": "large",
    "theme_high_contrast": false
  }'
```

---

## 🎨 **Color Schemes**

### **Default Blue Theme**
```css
:root {
    --theme-primary: #0d6efd;
    --theme-secondary: #6f42c1;
    --theme-gradient: linear-gradient(135deg, #0d6efd, #6f42c1);
}
```
**Best For**: Professional applications, corporate environments

### **Emerald Green Theme** 
```css
:root {
    --theme-primary: #10b981;
    --theme-secondary: #059669;
    --theme-gradient: linear-gradient(135deg, #10b981, #059669);
}
```
**Best For**: Environmental apps, health & wellness platforms

### **Purple Theme**
```css
:root {
    --theme-primary: #8b5cf6;
    --theme-secondary: #7c3aed;
    --theme-gradient: linear-gradient(135deg, #8b5cf6, #7c3aed);
}
```
**Best For**: Creative applications, modern interfaces

### **Amber Theme**
```css
:root {
    --theme-primary: #f59e0b;
    --theme-secondary: #d97706;
    --theme-gradient: linear-gradient(135deg, #f59e0b, #d97706);
}
```
**Best For**: Warm, inviting interfaces, educational platforms

---

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
