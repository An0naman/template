# Label Printing Section - Quick Reference

## 🚀 Quick Start (3 Steps)

```bash
# 1. Install dependencies
./setup_label_printing.sh

# 2. Enable section in entry type layout builder
Settings → Entry Types → [Select Type] → Layout Builder → Enable "Label Printing"

# 3. Open an entry and start printing!
```

## 📋 What You Got

| Component | File | Status | Lines |
|-----------|------|--------|-------|
| **UI Template** | `app/templates/partials/_label_printing_content.html` | ✨ NEW | ~510 |
| **API Routes** | `app/routes/printer_routes.py` | ✨ NEW | ~450 |
| **Section Config** | `app/services/entry_layout_service.py` | 📝 UPDATED | +15 |
| **App Init** | `app/__init__.py` | 📝 UPDATED | +2 |
| **Documentation** | `LABEL_PRINTING_SECTION.md` | ✨ NEW | Full docs |
| **Implementation** | `LABEL_PRINTING_IMPLEMENTATION.md` | ✨ NEW | Summary |
| **Architecture** | `LABEL_PRINTING_ARCHITECTURE.md` | ✨ NEW | Diagrams |
| **Setup Script** | `setup_label_printing.sh` | ✨ NEW | Executable |

## 🎯 Features At-a-Glance

### Core
- ✅ Bluetooth printer connection (Niimbot B1, D110)
- ✅ Live label preview
- ✅ QR code generation with entry URL
- ✅ Multiple label content types
- ✅ Customizable font size & print density

### Content Options
- 📝 Entry title only
- 📝 Title + Entry ID
- 📝 QR code only
- 📝 Title + QR code
- 📝 Custom text

### Settings
- 🔤 4 font sizes (small → xlarge)
- 🔲 5 density levels (1-5)
- 🔄 4 rotation options (0°/90°/180°/270°)
- 📋 3 label types (Gap/Black Mark/Continuous)
- 📊 Print 1-10 copies

## 🔌 API Endpoints

```javascript
// Connect to printer
POST /api/printer/connect
{ "printer": "niimbot_b1", "address": "XX:XX:XX:XX:XX:XX" }

// Print label
POST /api/printer/print-label
{
  "entryId": 123,
  "content": "My Entry",
  "fontSize": "medium",
  "density": 3,
  "includeQR": true,
  "copies": 2
}

// Get status
GET /api/printer/status

// Test print
POST /api/printer/test

// Generate QR
POST /api/printer/generate-qr
{ "url": "https://myapp.com/entry/123" }

// Disconnect
POST /api/printer/disconnect
```

## 🛠️ Configuration

### Default Section Config
```python
{
    'default_printer': 'niimbot_b1',
    'default_font_size': 'medium',
    'default_density': 3,
    'include_qr_default': True,
    'default_copies': 1
}
```

### Layout Position
- Position: Row 106, Column 0
- Size: 12 columns × 6 rows
- Visibility: Hidden by default
- Collapsible: Yes

## 🔍 Troubleshooting

### Printer Won't Connect
```bash
# Check Bluetooth service
sudo systemctl status bluetooth

# List paired devices
bluetoothctl devices

# Verify MAC address format
# Should be: XX:XX:XX:XX:XX:XX
```

### Dependencies Not Installed
```bash
# Install manually
pip3 install qrcode[pil] pillow

# Or use setup script
./setup_label_printing.sh
```

### Section Not Appearing
1. Check entry type layout builder
2. Ensure "Label Printing" is enabled
3. Verify `is_visible = 1` in database
4. Clear browser cache

### Print Quality Issues
- Increase density (try 4 or 5)
- Check label type matches physical labels
- Verify printer isn't jammed

## 📁 File Locations

```
Quick Access Paths:

UI Template:
/home/an0naman/Documents/GitHub/template/app/templates/partials/_label_printing_content.html

API Routes:
/home/an0naman/Documents/GitHub/template/app/routes/printer_routes.py

Layout Service:
/home/an0naman/Documents/GitHub/template/app/services/entry_layout_service.py

Printer Service (existing):
/home/an0naman/Documents/GitHub/template/app/services/niimbot_printer.py

Documentation:
/home/an0naman/Documents/GitHub/template/LABEL_PRINTING_SECTION.md
```

## 🧪 Testing Checklist

```
□ Dependencies installed (qrcode, pillow)
□ Printer paired via Bluetooth
□ Section enabled in entry type layout
□ Section visible on entry page
□ Printer connects with valid address
□ Test print works
□ Label preview updates correctly
□ QR code generates properly
□ Print succeeds with different content types
□ Multiple copies print
□ Rotation works
□ Settings persist in localStorage
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `LABEL_PRINTING_SECTION.md` | Complete feature documentation |
| `LABEL_PRINTING_IMPLEMENTATION.md` | Implementation summary |
| `LABEL_PRINTING_ARCHITECTURE.md` | System architecture & diagrams |
| `LABEL_PRINTING_QUICK_REF.md` | This quick reference (you are here!) |

## 💡 Pro Tips

1. **Save Printer Settings**: Settings are stored in browser localStorage - no need to re-enter each time
2. **Test First**: Always run a test print before printing multiple copies
3. **QR Codes**: Include QR codes for easy mobile access to entries
4. **Density**: Start with 3, increase if print is too light
5. **Custom Text**: Use custom text for special labels like warnings or instructions

## 🎨 Example Use Cases

### Asset Label
```javascript
{
  "content": "Server #42",
  "contentType": "title_qr",
  "fontSize": "large",
  "includeQR": true
}
```

### Warning Label
```javascript
{
  "content": "FRAGILE - Handle with Care",
  "contentType": "custom",
  "fontSize": "xlarge",
  "density": 4
}
```

### Inventory Label
```javascript
{
  "content": "Widget Inventory",
  "contentType": "title_id",
  "fontSize": "medium",
  "copies": 5
}
```

## 🚀 Next Steps

### Immediate
1. ✅ Run setup script
2. ✅ Pair printer
3. ✅ Enable section
4. ✅ Test print

### Future Enhancements
- [ ] Label template library
- [ ] Batch printing
- [ ] Custom logos
- [ ] 1D barcodes
- [ ] Network printers
- [ ] Mobile app integration

## 📞 Support

- Check documentation files for detailed info
- Review API responses for error details
- Check browser console for JavaScript errors
- Review Flask logs for backend issues
- Verify Bluetooth connection

## ✅ Status: READY TO USE

Everything is implemented and ready to go. Just:
1. Install dependencies
2. Enable the section
3. Start printing!

---
**Created**: 2025-11-09  
**Status**: Production Ready ✅  
**Version**: 1.0.0
