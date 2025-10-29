# Testing Entry Layout Builder

## How to Test the Header Section Visibility

### Step 1: Configure the Layout
1. Navigate to **Manage Entry Types** in your app
2. Find an entry type (e.g., "batch")
3. Click the **"Configure Layout"** button (grid icon)

### Step 2: Hide the Header Section
1. In the layout grid, find the **"Entry Details"** section (this is the header)
2. Click the **eye icon** (👁️) on that section to hide it
3. The section should gray out or show as hidden
4. Click **"Save Layout"** button
5. You should see a success message

### Step 3: Test on an Entry
1. Go back to the main page
2. Click on any entry of that type (e.g., a batch)
3. **The header section should now be completely hidden!**
   - No title
   - No status badge
   - No dates
   - No description
   - No action buttons

### Step 4: Show it Again
1. Go back to the layout builder
2. Click the eye icon again to show the header
3. Save layout
4. Refresh the entry page
5. **Header should reappear!**

## What's Actually Hidden

When you hide the header section, these elements disappear:
- Entry title (H1)
- Edit/Delete/Back buttons
- Labels button
- Entry type display
- Status badge
- Created date
- Intended/Actual end dates (if applicable)
- Description text area
- Progress timeline (if applicable)
- Wikipedia search integration
- AI description generation buttons

## Debugging

If it's not working, check:

1. **Layout saved?** - Check the database:
```bash
docker exec template python -c "
from app.services.entry_layout_service import EntryLayoutService
layout = EntryLayoutService.get_layout_for_entry_type(6)  # Change 6 to your entry type ID
header = [s for s in layout['sections'] if s['section_type'] == 'header'][0]
print(f\"Header visible: {header['is_visible']}\")
"
```

2. **Section config passed?** - Check browser console for errors

3. **Correct entry type?** - Make sure you're viewing an entry of the type you configured

## Expected Behavior

✅ **Working:**
- Layout builder loads with 13 sections
- Can drag sections around
- Can resize sections
- Can toggle visibility with eye icon
- Can edit section properties
- Save layout succeeds
- Header section shows/hides based on configuration

❌ **Not Yet Working:**
- Other sections (notes, sensors, etc.) still show regardless of layout
- Section ordering (all sections show in template order)
- Section sizing (uses default responsive sizes)

## Next: Configure Other Sections

To make other sections configurable, we need to wrap them in the template similar to header.

The pattern is:
```jinja2
{% if section_visible.get('section_name', {}).get('visible', True) %}
    <!-- Section content -->
{% endif %}
```

Sections to wrap:
- `notes` - Notes list and add note form
- `sensors` - Sensor data charts
- `relationships` - Related entries
- `labels` - Label printing
- `reminders` - Reminder management
- `ai_assistant` - AI chat
- `attachments` - File uploads
- `form_fields` - Custom fields

Each takes about 5 minutes to wrap.

