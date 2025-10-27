# Entry Layout Builder - Quick Start Guide 🚀

## Installation (Docker)

```bash
# Step 1: Run migration in Docker container
docker exec -it <your-container-name> .venv/bin/python migrations/add_entry_layout_tables.py

# Step 2: Restart the application
docker-compose restart

# That's it! The feature is ready to use.
```

## How to Access

1. Navigate to **Settings** → **Manage Entry Types**
2. Look for the green **📐 Configure Layout** button next to each entry type
3. Click it to open the Layout Builder

## Quick Usage

| Action | How To |
|--------|--------|
| **Enable Editing** | Click "Edit Layout" button |
| **Add Section** | Click section in left palette |
| **Move Section** | Drag section header |
| **Resize Section** | Drag section corners |
| **Configure** | Click gear icon on section |
| **Hide/Show** | Click eye icon on section |
| **Delete** | Click trash icon (edit mode only) |
| **Save** | Click "Save Layout" button |
| **Reset** | Click "Reset to Default" button |

## Available Sections

- Header (entry details)
- Notes
- Relationships  
- Labels
- Sensors
- Reminders
- AI Assistant
- Attachments
- Custom Fields
- QR Code
- Label Printing
- Timeline

## Files Created

1. ✅ `migrations/add_entry_layout_tables.py`
2. ✅ `app/services/entry_layout_service.py`
3. ✅ `app/api/entry_layout_api.py`
4. ✅ `app/templates/entry_layout_builder.html`
5. ✅ `app/static/js/entry_layout_builder.js`

## Files Modified

1. ✅ `app/__init__.py` (blueprint registered)
2. ✅ `app/routes/main_routes.py` (route added)
3. ✅ `app/templates/manage_entry_types.html` (button added)

## Next: Entry Renderer

To make entry detail pages use the configured layouts, you'll need to:

1. Create `app/static/js/entry_layout_renderer.js`
2. Modify `app/templates/entry_detail.html` to load and render layouts dynamically
3. Implement section factory pattern for rendering each section type

This is phase 2 of the implementation (optional - entries still work normally without it).

---

**Ready to use!** Run the migration command above to get started. 🎉
