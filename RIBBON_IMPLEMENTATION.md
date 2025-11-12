# Universal App Ribbon - Implementation Guide

## Overview
This document describes the universal ribbon component that has been added to the application. The ribbon provides consistent branding and navigation across all pages, with full theme support.

## Components Created

### 1. VERSION File (`/VERSION`)
- Contains the current application version (format: `MAJOR.MINOR.PATCH`)
- Auto-incremented by git pre-push hook when pushing to main branch
- Initial version: `1.0.0`

### 2. Ribbon Component (`/app/templates/components/ribbon.html`)
- Universal navigation bar displayed at the top of all pages
- Features:
  - App title/branding
  - About button to display version information
  - Fully responsive design
  - Theme-aware styling

### 3. About Modal (`/app/templates/components/about_modal.html`)
- Modal dialog displaying:
  - Application name and version
  - Current theme information (light/dark mode)
  - System information (database, framework)
- Accessible via ribbon's About button

### 4. Ribbon Styles (`/app/static/ribbon.css`)
- Theme-aware CSS styles
- Responsive design for mobile, tablet, and desktop
- Adapts colors based on current theme (light/dark mode)
- Print-friendly (hidden when printing)

### 5. Version Context Processor (`/app/__init__.py`)
- Automatically injects `app_version` into all templates
- Reads version from VERSION file
- Fallback to '1.0.0' if file not found

### 6. Git Pre-Push Hook (`/.git/hooks/pre-push`)
- Automatically increments patch version when pushing to main/master branch
- Updates both VERSION file and app.json
- Commits changes with amended commit

## Usage

### Adding Ribbon to a Page

1. **Include CSS in `<head>`:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='ribbon.css') }}">
```

2. **Add Ribbon at start of `<body>`:**
```html
<body>
    {% include 'components/ribbon.html' %}
    
    <!-- Your page content here -->
</body>
```

3. **Add About Modal before closing `</body>`:**
```html
    <!-- About Modal -->
    {% include 'components/about_modal.html' %}
</body>
</html>
```

### Example Implementation

See `app/templates/index.html` and `app/templates/settings.html` for complete examples.

## Version Management

### Manual Version Update
Edit the VERSION file:
```bash
echo "2.0.0" > VERSION
```

### Automatic Version Update
The version is automatically incremented when you push to the main branch:
```bash
git add .
git commit -m "Your changes"
git push origin main  # Version auto-increments from 1.0.0 to 1.0.1
```

### Version Format
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

The git hook automatically increments the PATCH version. For MAJOR or MINOR changes, update VERSION manually.

## Theme Integration

The ribbon automatically respects the application's theme settings:

- **Colors**: Uses `--theme-primary` and `--theme-primary-hover` CSS variables
- **Dark Mode**: Adapts button opacity and shadows
- **Responsive**: Hides button text on mobile devices
- **Accessible**: Maintains contrast ratios in all themes

## Customization

### Changing Ribbon Colors
The ribbon uses theme CSS variables. To customize, modify your theme settings or override in ribbon.css:

```css
.app-ribbon {
    background: linear-gradient(135deg, #custom-color-1, #custom-color-2);
}
```

### Adding More Buttons
Edit `app/templates/components/ribbon.html`:

```html
<div class="ribbon-actions">
    <button type="button" class="ribbon-btn" onclick="yourFunction()">
        <i class="fas fa-icon"></i>
        <span class="ribbon-btn-text">Button Text</span>
    </button>
    <!-- Existing About button -->
</div>
```

### Modifying About Modal
Edit `app/templates/components/about_modal.html` to add more sections or information.

## Files Modified/Created

### Created:
- `/VERSION` - Version file
- `/app/templates/components/ribbon.html` - Ribbon component
- `/app/templates/components/about_modal.html` - About modal component
- `/app/static/ribbon.css` - Ribbon styles
- `/.git/hooks/pre-push` - Version auto-increment script

### Modified:
- `/app/__init__.py` - Added version context processor
- `/app.json` - Updated version to semantic versioning format
- `/app/templates/index.html` - Added ribbon and modal includes
- `/app/templates/settings.html` - Added ribbon and modal includes

## Benefits

1. **Consistent Branding**: Same header across all pages
2. **Version Visibility**: Easy access to app version for users
3. **Theme Compliance**: Automatically adapts to light/dark modes
4. **Automated Versioning**: No manual version updates needed
5. **Extensible**: Easy to add more buttons or features
6. **Responsive**: Works on all device sizes

## Next Steps

To add the ribbon to additional pages:
1. Include the CSS file in the page's `<head>`
2. Add the ribbon include after `<body>`
3. Add the modal include before `</body>`

That's it! The version will automatically be available in all templates.
