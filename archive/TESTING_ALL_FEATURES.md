# Testing All Entry Layout Features

Now that we've implemented all features on the header section, test each one:

## Feature 1: Visibility ✅ (Already Tested)

**Test:**
1. Hide header section in layout builder
2. Entry page shows no header
3. Show header section again
4. Entry page shows header

## Feature 2: Custom Title 🆕

**Test:**
1. Go to layout builder
2. Click gear icon on "Entry Details" section
3. Change title to something custom like "My Custom Header"
4. Click "Save Properties"
5. Click "Save Layout"
6. View an entry of that type
7. **Look for a collapsible section** with title "My Custom Header" (if collapsible is enabled)

**Note:** Custom title only shows if section is collapsible. Otherwise the entry title is the H1.

## Feature 3: Make it Collapsible 🆕

**Test:**
1. Go to layout builder
2. Click gear icon on "Entry Details" section
3. Toggle "Collapsible" switch to ON
4. Click "Save Properties"
5. Click "Save Layout"  
6. View an entry
7. **You should see:**
   - A section header with the configured title
   - A collapse/expand button (chevron icon)
   - Click it to collapse/expand the header content

## Feature 4: Default Collapsed State 🆕

**Test:**
1. Go to layout builder
2. Make sure "Collapsible" is ON
3. Toggle "Start Collapsed" switch to ON
4. Click "Save Properties"
5. Click "Save Layout"
6. View an entry
7. **Header section should start collapsed** (hidden)
8. Click the chevron button to expand it

## Feature 5: All Features Combined 🎯

**Perfect Configuration Test:**

1. **Configure:**
   - Title: "Entry Information"
   - Collapsible: ON
   - Start Collapsed: ON
   - Visible: ON
   - Width: 12
   - Height: 4

2. **Expected Result:**
   - Entry page loads with collapsed "Entry Information" section
   - Click chevron to expand
   - All entry details inside
   - Section takes full width

## What Each Feature Does

### Visibility
- **ON**: Section appears on entry page
- **OFF**: Section completely hidden

### Custom Title
- Only visible when section is collapsible
- Replaces default "Entry Details" text
- Shows in section header bar

### Collapsible
- **ON**: Adds header bar with title and collapse button
- **OFF**: Section always expanded, no header bar

### Start Collapsed
- Only works if Collapsible is ON
- **ON**: Section hidden by default, click to expand
- **OFF**: Section expanded by default, click to collapse

### Width/Height
- Controls section size in grid
- Width: 1-12 columns (12 = full width)
- Height: Number of rows (each ~80px)

## Debugging

If features don't work:

**Check section config:**
```bash
docker exec template python -c "
from app.services.entry_layout_service import EntryLayoutService
layout = EntryLayoutService.get_layout_for_entry_type(6)
header = [s for s in layout['sections'] if s['section_type'] == 'header'][0]
print('Header config:')
print(f\"  Visible: {header['is_visible']}\")
print(f\"  Title: {header['title']}\")
print(f\"  Collapsible: {header['is_collapsible']}\")
print(f\"  Collapsed: {header['default_collapsed']}\")
"
```

**Common Issues:**

1. **Custom title not showing**: Make sure collapsible is ON
2. **Can't collapse**: Make sure collapsible is ON
3. **Not starting collapsed**: Make sure both collapsible and start collapsed are ON
4. **Changes not applying**: Clear browser cache and hard refresh (Ctrl+Shift+R)

## Next Step: Apply to All Sections

Once you've tested and confirmed ALL features work on the header, we'll use this EXACT same pattern for:

- Notes
- Sensors  
- Relationships
- Labels
- Reminders
- AI Assistant
- Attachments
- Form Fields
- QR Code
- Label Printing
- Relationship Opportunities
- Timeline

Each section will get:
✅ Show/Hide
✅ Custom Title
✅ Collapsible
✅ Start Collapsed
✅ Configurable Size (via layout builder)

**Ready to test? Try all 5 features and let me know if everything works!**

