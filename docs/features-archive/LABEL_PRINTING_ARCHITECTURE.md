# Label Printing Section - Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         LABEL PRINTING ARCHITECTURE                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. USER INTERFACE (Browser)                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Entry Detail Page (/entry/<id>)                                    │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │ Header Section                                              │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │ AI Assistant Section                                        │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │ Sensors Section                  Notes Section               │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │  ┌─────────────────────────────────────────────────────────────┐  │    │
│  │  │ ⭐ LABEL PRINTING SECTION ⭐                                 │  │    │
│  │  │                                                              │  │    │
│  │  │  ┌────────────────────────────────────────────────────┐    │  │    │
│  │  │  │ Printer Status Card                                │    │  │    │
│  │  │  │ - Select Printer (B1/D110)                         │    │  │    │
│  │  │  │ - Enter Bluetooth Address                          │    │  │    │
│  │  │  │ - Connect/Disconnect Buttons                       │    │  │    │
│  │  │  │ - Status Badge (Connected/Not Connected)           │    │  │    │
│  │  │  └────────────────────────────────────────────────────┘    │  │    │
│  │  │                                                              │  │    │
│  │  │  ┌────────────────────────────────────────────────────┐    │  │    │
│  │  │  │ Label Design Card                                  │    │  │    │
│  │  │  │ - Content Type Selector                            │    │  │    │
│  │  │  │ - Font Size Dropdown                               │    │  │    │
│  │  │  │ - Density Selector (1-5)                           │    │  │    │
│  │  │  │ - QR Code Checkbox                                 │    │  │    │
│  │  │  │ - Live Preview Panel                               │    │  │    │
│  │  │  └────────────────────────────────────────────────────┘    │  │    │
│  │  │                                                              │  │    │
│  │  │  ┌────────────────────────────────────────────────────┐    │  │    │
│  │  │  │ Print Settings Card                                │    │  │    │
│  │  │  │ - Number of Copies (1-10)                          │    │  │    │
│  │  │  │ - Rotation Selector (0°/90°/180°/270°)             │    │  │    │
│  │  │  │ - Label Type (Gap/Black Mark/Continuous)           │    │  │    │
│  │  │  │ - Print/Test/Generate QR Buttons                   │    │  │    │
│  │  │  │ - Status Messages                                  │    │  │    │
│  │  │  └────────────────────────────────────────────────────┘    │  │    │
│  │  └─────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  JavaScript in Template:                                                    │
│  - Event handlers for buttons                                               │
│  - AJAX calls to API endpoints                                              │
│  - Live preview updates                                                     │
│  - localStorage for printer settings                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP Requests
                                      │ (AJAX/Fetch)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. FLASK BACKEND                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Flask App (__init__.py)                                            │    │
│  │                                                                     │    │
│  │  Registers Blueprints:                                             │    │
│  │  - main_bp                                                          │    │
│  │  - maintenance_bp                                                   │    │
│  │  - printer_bp ⭐ NEW                                               │    │
│  │  - [... other blueprints ...]                                       │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Printer Blueprint (printer_routes.py)                              │    │
│  │                                                                     │    │
│  │  API Endpoints:                                                     │    │
│  │  POST   /api/printer/connect          ─┐                           │    │
│  │  POST   /api/printer/disconnect        │                           │    │
│  │  GET    /api/printer/status            ├─ Connection Management    │    │
│  │  POST   /api/printer/test              │                           │    │
│  │  POST   /api/printer/print-label       ├─ Printing Operations      │    │
│  │  POST   /api/printer/generate-qr      ─┘                           │    │
│  │                                                                     │    │
│  │  Functions:                                                         │    │
│  │  - connect_printer()      → Stores connection config               │    │
│  │  - disconnect_printer()   → Clears connection                      │    │
│  │  - printer_status()       → Returns connection info                │    │
│  │  - test_print()           → Sends test pattern                     │    │
│  │  - print_label()          → Creates & prints label                 │    │
│  │  - generate_qr()          → Creates QR code image                  │    │
│  │  - create_label_image()   → PIL image generation                   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                          │                                                   │
│                          │ Uses                                              │
│                          ▼                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Niimbot Printer Service (niimbot_printer.py) - EXISTING           │    │
│  │                                                                     │    │
│  │  Classes:                                                           │    │
│  │  - NiimbotPrinter                                                   │    │
│  │  - NiimbotPacket                                                    │    │
│  │                                                                     │    │
│  │  Methods:                                                           │    │
│  │  - connect()              → Bluetooth RFCOMM connection            │    │
│  │  - disconnect()           → Close connection                        │    │
│  │  - print_image()          → Send image to printer                  │    │
│  │  - set_density()          → Configure print density                │    │
│  │  - set_label_type()       → Configure label type                   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                          │                                                   │
│                          │ Sends packets via                                │
│                          ▼                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Python Libraries                                                    │    │
│  │                                                                     │    │
│  │  - qrcode        → QR code generation                              │    │
│  │  - PIL (Pillow)  → Image creation/manipulation                     │    │
│  │  - socket        → Bluetooth RFCOMM communication                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Bluetooth RFCOMM
                                      │ Packets
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. HARDWARE                                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ Niimbot Label Printer                                              │    │
│  │                                                                     │    │
│  │  Supported Models:                                                  │    │
│  │  - Niimbot B1       (Compact)                                      │    │
│  │  - Niimbot D110     (Desktop)                                      │    │
│  │                                                                     │    │
│  │  Connection:                                                        │    │
│  │  - Bluetooth Classic (RFCOMM)                                      │    │
│  │  - MAC Address: XX:XX:XX:XX:XX:XX                                  │    │
│  │                                                                     │    │
│  │  Label Specs:                                                       │    │
│  │  - Width: 384 pixels (standard)                                    │    │
│  │  - Height: Variable                                                │    │
│  │  - Color: 1-bit (B&W)                                              │    │
│  │  - Type: Thermal                                                    │    │
│  │                                                                     │    │
│  │  ┌──────────────────────────────────────┐                         │    │
│  │  │                                       │                         │    │
│  │  │  ┌─────────────────────────────────┐ │                         │    │
│  │  │  │ Entry Title Here                │ │  ← Printed Label        │    │
│  │  │  │                                 │ │                         │    │
│  │  │  │  ┌────────┐                     │ │                         │    │
│  │  │  │  │░░░░░░░░│  QR Code            │ │                         │    │
│  │  │  │  │░░░░░░░░│  (Optional)         │ │                         │    │
│  │  │  │  └────────┘                     │ │                         │    │
│  │  │  └─────────────────────────────────┘ │                         │    │
│  │  └──────────────────────────────────────┘                         │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. DATA FLOW                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Action Flow:                                                          │
│                                                                              │
│  1. User Opens Entry  →  2. Section Rendered  →  3. User Configures        │
│     Detail Page           (if enabled)             Label Design             │
│                                                                              │
│  4. User Clicks      →  5. AJAX Request    →  6. API Processes             │
│     "Print Label"        to /api/printer       Request                      │
│                          /print-label                                        │
│                                                                              │
│  7. create_label_   →  8. NiimbotPrinter  →  9. Printer Receives           │
│     image() creates     sends via             Packets                       │
│     PIL Image           Bluetooth                                           │
│                                                                              │
│  10. Label Prints   →  11. Status          →  12. UI Shows                 │
│      Successfully        Returned              "Success!"                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. CONFIGURATION & DATABASE                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EntryLayoutSection Table:                                                  │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ id | layout_id | section_type    | config (JSON)               │        │
│  ├────────────────────────────────────────────────────────────────┤        │
│  │ 42 | 1         | label_printing  | {                           │        │
│  │    |           |                 |   "default_printer": "b1",  │        │
│  │    |           |                 |   "default_font": "medium", │        │
│  │    |           |                 |   "default_density": 3,     │        │
│  │    |           |                 |   "include_qr": true        │        │
│  │    |           |                 | }                           │        │
│  └────────────────────────────────────────────────────────────────┘        │
│                                                                              │
│  Default Section Config (EntryLayoutService):                               │
│  {                                                                           │
│    'title': 'Label Printing',                                               │
│    'position_x': 0,                                                          │
│    'position_y': 106,                                                        │
│    'width': 12,                                                              │
│    'height': 6,                                                              │
│    'is_visible': 0,  ← Hidden by default, enable per entry type             │
│    'is_collapsible': 1,                                                      │
│    'display_order': 106                                                      │
│  }                                                                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. FILE STRUCTURE                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  app/                                                                        │
│  ├── __init__.py                    ✏️ Modified (register printer_bp)      │
│  ├── routes/                                                                │
│  │   ├── main_routes.py             ✓ Existing                             │
│  │   ├── maintenance_routes.py      ✓ Existing                             │
│  │   └── printer_routes.py          ⭐ NEW (Label printing API)            │
│  ├── services/                                                              │
│  │   ├── entry_layout_service.py    ✏️ Modified (added section config)    │
│  │   └── niimbot_printer.py         ✓ Existing (printer communication)     │
│  └── templates/                                                             │
│      ├── macros/                                                            │
│      │   └── entry_sections.html    ✓ Already had macro                    │
│      └── partials/                                                          │
│          └── _label_printing_       ⭐ NEW (Complete UI)                   │
│              content.html                                                    │
│                                                                              │
│  Documentation:                                                             │
│  ├── LABEL_PRINTING_SECTION.md              ⭐ NEW (Feature docs)          │
│  ├── LABEL_PRINTING_IMPLEMENTATION.md       ⭐ NEW (Implementation guide)  │
│  └── setup_label_printing.sh                ⭐ NEW (Setup script)          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Key Integration Points

### 1. **Modular Design**
- Section is completely self-contained
- Can be enabled/disabled per entry type
- No modifications to existing templates required
- Uses established section macro pattern

### 2. **API Architecture**
- RESTful endpoints under `/api/printer/*`
- Clean separation: Routes → Service → Hardware
- Error handling at each layer
- JSON responses for easy consumption

### 3. **Configuration System**
- Database-driven layout configuration
- Default settings in `EntryLayoutService`
- User preferences in localStorage
- Per-entry-type customization

### 4. **Hardware Communication**
- Leverages existing `niimbot_printer.py`
- Bluetooth RFCOMM protocol
- Packet-based communication
- Support for multiple printer models

### 5. **User Experience**
- Live preview of labels
- Real-time status feedback
- Persistent connection settings
- Intuitive interface design
