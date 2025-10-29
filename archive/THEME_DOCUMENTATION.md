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
| **Custom** | User-defined | User-defined | Fully customizable colors with light/dark mode support |

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

### **🎨 Custom Theme Colors**
The **Custom** theme option provides complete control over both light and dark mode appearances:

#### **🎯 Custom Color Palette**
When selecting the "Custom" theme, you can customize:
- **Primary Color**: Main action buttons and links
- **Primary Hover Color**: Hover state for primary elements
- **Secondary Color**: Secondary buttons and muted text
- **Success Color**: Success messages and confirmations
- **Danger Color**: Error messages and delete buttons
- **Warning Color**: Warning messages and caution alerts
- **Info Color**: Information messages and highlights

#### **☀️ Light Mode Customization**
- **Background Color**: Main page background
- **Card Background**: Content cards and containers
- **Surface Background**: Secondary surfaces and form elements
- **Text Color**: Primary text and headings
- **Muted Text Color**: Secondary text and descriptions
- **Border Color**: Borders and dividers

#### **🌙 Dark Mode Customization**
- **Background Color**: Dark theme main background
- **Card Background**: Dark theme content cards
- **Surface Background**: Dark theme secondary surfaces
- **Text Color**: Dark theme primary text
- **Muted Text Color**: Dark theme secondary text
- **Border Color**: Dark theme borders and dividers

#### **📦 Section Styling Options**
Customize the visual appearance of content sections, filter areas, and entry cards:

**Border Styles:**
- **Rounded** (Default): Standard rounded corners (0.75rem radius)
- **Sharp**: No border radius for a modern, angular look
- **Subtle**: Slightly rounded corners (0.375rem radius)
- **Bold**: Pronounced rounded corners (1.25rem radius)

**Section Spacing:**
- **Compact**: Reduced padding and margins (1rem)
- **Normal** (Default): Standard spacing (1.5rem)
- **Spacious**: Increased spacing for better readability (2rem)

**Background Effects:**
- **Flat**: No shadows, seamless blend with page background
- **Subtle** (Default): Light shadow and clear borders
- **Elevated**: Strong shadows for a floating card effect
- **Glassmorphic**: Semi-transparent background with blur effects

#### **✨ Advanced Features**
- **Real-time Preview**: See changes as you make them
- **Color Synchronization**: Color picker and hex input stay in sync
- **Reset Options**: Restore default values with one click
- **Persistence**: Custom colors saved across sessions
- **Automatic Application**: Page reloads automatically to apply changes
- **Section Style Preview**: Interactive preview showing how styling affects sections

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
    },
    'custom': {
        'primary': 'user-defined',
        'secondary': 'user-defined',
        'name': 'Custom',
        'supports_full_customization': True
    }
}
```

#### **Custom Theme Configuration**
```python
# Custom color palette (when theme = 'custom')
CUSTOM_COLORS = {
    'primary': '#0d6efd',
    'primary_hover': '#0b5ed7', 
    'secondary': '#6c757d',
    'success': '#198754',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#0dcaf0'
}

# Custom light mode colors
CUSTOM_LIGHT_MODE = {
    'bg_body': '#ffffff',
    'bg_card': '#ffffff',
    'bg_surface': '#f8f9fa',
    'text': '#212529',
    'text_muted': '#6c757d',
    'border': '#dee2e6'
}

# Custom dark mode colors  
CUSTOM_DARK_MODE = {
    'bg_body': '#0d1117',
    'bg_card': '#161b22',
    'bg_surface': '#21262d',
    'text': '#f0f6fc',
    'text_muted': '#8b949e',
    'border': '#30363d'
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

#### **Section Styling Configuration**
```python
SECTION_STYLES = {
    'border_style': 'rounded',  # rounded, sharp, subtle, bold
    'spacing': 'normal',        # compact, normal, spacious
    'background': 'subtle'      # flat, subtle, elevated, glassmorphic
}
```

#### **Configuration via Web Interface**
1. **Theme Selection**: Choose from 5 color schemes (4 pre-built + 1 custom)
2. **Dark Mode Toggle**: Enable/disable dark mode
3. **Font Size**: Select from 4 typography options
4. **High Contrast**: Toggle high contrast mode
5. **Section Styling**: Customize appearance of content sections
   - **Border Style**: 4 options for section corner rounding
   - **Section Spacing**: 3 options for padding and margins
   - **Background Style**: 4 options for shadows and effects
6. **Custom Colors** (when Custom theme selected):
   - **Color Palette**: 7 customizable theme colors
   - **Light Mode**: 6 customizable light mode interface elements
   - **Dark Mode**: 6 customizable dark mode interface elements
   - **Reset Options**: Restore defaults for any section
7. **Live Preview**: See changes instantly with section style preview
8. **Auto-Reload**: Page automatically refreshes to apply custom colors

#### **Configuration via API**
```bash
# Update basic theme settings
curl -X POST http://localhost:5000/api/theme_settings \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "purple",
    "dark_mode": true,
    "font_size": "large",
    "high_contrast": false
  }'

# Update with custom colors
curl -X POST http://localhost:5000/api/theme_settings \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "custom",
    "dark_mode": true,
    "font_size": "normal",
    "high_contrast": false,
    "custom_colors": {
      "primary": "#ff6b35",
      "primary_hover": "#e55a2e",
      "secondary": "#6c757d",
      "success": "#28a745",
      "danger": "#dc3545",
      "warning": "#ffc107",
      "info": "#17a2b8"
    },
    "custom_light_mode": {
      "bg_body": "#f8f9fa",
      "bg_card": "#ffffff",
      "bg_surface": "#e9ecef",
      "text": "#212529",
      "text_muted": "#6c757d",
      "border": "#dee2e6"
    },
    "custom_dark_mode": {
      "bg_body": "#1a1a1a",
      "bg_card": "#2d2d2d",
      "bg_surface": "#404040",
      "text": "#ffffff",
      "text_muted": "#adb5bd",
      "border": "#495057"
    }
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

### **Custom Theme**
```css
:root {
    /* User-defined color palette */
    --theme-primary: var(--custom-primary, #0d6efd);
    --theme-primary-hover: var(--custom-primary-hover, #0b5ed7);
    --theme-secondary: var(--custom-secondary, #6c757d);
    --theme-success: var(--custom-success, #198754);
    --theme-danger: var(--custom-danger, #dc3545);
    --theme-warning: var(--custom-warning, #ffc107);
    --theme-info: var(--custom-info, #0dcaf0);
    
    /* Dynamic light/dark mode colors */
    --theme-bg-body: var(--mode-bg-body);
    --theme-bg-card: var(--mode-bg-card);
    --theme-bg-surface: var(--mode-bg-surface);
    --theme-text: var(--mode-text);
    --theme-text-muted: var(--mode-text-muted);
    --theme-border: var(--mode-border);
}
```
**Best For**: Brand-specific applications, unique visual identities, complete design control

**Features**:
- 🎨 **7 Customizable Theme Colors**: Full control over primary, secondary, success, danger, warning, info, and hover colors
- ☀️ **6 Light Mode Elements**: Background, cards, surfaces, text, muted text, and borders
- 🌙 **6 Dark Mode Elements**: Complete dark theme customization
- 🔄 **Real-time Updates**: See changes instantly with live preview
- 💾 **Persistent Storage**: Custom colors saved across sessions
- ↩️ **Reset Options**: Restore defaults for any color category

---

Theme parameters:
- `theme`: Color theme (default, emerald, purple, amber, custom)
- `dark_mode`: Dark mode enabled (true/false)
- `font_size`: Base font size (small, normal, large, extra-large)
- `high_contrast`: High contrast mode (true/false)
- `section_styles`: Section styling options
  - `border_style`: Border corner style (rounded, sharp, subtle, bold)
  - `spacing`: Section spacing (compact, normal, spacious)
  - `background`: Background effect (flat, subtle, elevated, glassmorphic)
- `custom_colors`: Custom color palette (when theme = 'custom')
  - `primary`, `primary_hover`, `secondary`, `success`, `danger`, `warning`, `info`
- `custom_light_mode`: Light mode interface colors
  - `bg_body`, `bg_card`, `bg_surface`, `text`, `text_muted`, `border`
- `custom_dark_mode`: Dark mode interface colors
  - `bg_body`, `bg_card`, `bg_surface`, `text`, `text_muted`, `border`

### API Endpoints

#### GET `/api/theme_settings`
Retrieve current theme settings.

**Response (Basic Theme):**
```json
{
    "theme": "default",
    "dark_mode": false,
    "font_size": "normal",
    "high_contrast": false,
    "section_styles": {
        "border_style": "rounded",
        "spacing": "normal",
        "background": "subtle"
    },
    "custom_colors": {},
    "custom_light_mode": {},
    "custom_dark_mode": {}
}
```

**Response (Custom Theme):**
```json
{
    "theme": "custom",
    "dark_mode": true,
    "font_size": "large",
    "high_contrast": false,
    "section_styles": {
        "border_style": "bold",
        "spacing": "spacious",
        "background": "elevated"
    },
    "custom_colors": {
        "primary": "#ff6b35",
        "primary_hover": "#e55a2e",
        "secondary": "#6c757d",
        "success": "#28a745",
        "danger": "#dc3545",
        "warning": "#ffc107",
        "info": "#17a2b8"
    },
    "custom_light_mode": {
        "bg_body": "#f8f9fa",
        "bg_card": "#ffffff",
        "bg_surface": "#e9ecef",
        "text": "#212529",
        "text_muted": "#6c757d",
        "border": "#dee2e6"
    },
    "custom_dark_mode": {
        "bg_body": "#1a1a1a",
        "bg_card": "#2d2d2d",
        "bg_surface": "#404040",
        "text": "#ffffff",
        "text_muted": "#adb5bd",
        "border": "#495057"
    }
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
    "high_contrast": false,
    "section_styles": {
        "border_style": "bold",
        "spacing": "spacious",
        "background": "elevated"
    }
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

- ✅ **Custom color picker for advanced users** - *Implemented with full light/dark mode customization*
- 🔮 **Theme scheduling** (auto dark mode at sunset)
- 🔤 **Additional font family options**
- 📦 **Import/export theme configurations**
- 👁️ **Enhanced preview modes** (mobile, tablet views)
- 🎨 **Color palette suggestions** based on brand colors
- 🔗 **Theme sharing** via URL parameters
- 📊 **Accessibility scoring** for custom color combinations
