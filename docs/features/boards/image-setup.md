# Board Image Setup Guide

## Current Status

✅ **SVG Placeholder Active**
- File: `app/static/images/boards/esp32-wroom-32.svg`
- Type: Vector graphic (scalable)
- Status: Working placeholder that displays board layout

## Upgrading to Photo (Optional)

If you want to use the actual board photo from the attachment:

### Step 1: Save the Image
1. Right-click the ESP32 board image from the chat attachment
2. Save as: `esp32-wroom-32.png`
3. Place in: `app/static/images/boards/`

### Step 2: Automatic Fallback
The system will automatically:
1. Try to load the PNG first (better quality)
2. Fall back to SVG if PNG not found
3. Show styled placeholder if both fail

### Step 3: Adjust Coordinates (if needed)
If the photo has different dimensions, edit `app/static/js/board-configs.js`:

```javascript
'ESP32-WROOM-32': {
    image: '/static/images/boards/esp32-wroom-32.png',
    fallbackImage: '/static/images/boards/esp32-wroom-32.svg',
    chipOverlay: {
        x: 85,    // Adjust these based on your photo
        y: 90,    // Measure from top-left
        width: 120,
        height: 140
    },
    pins: [
        { pin: 2, name: 'LED', x: 275, y: 105, ... },
        // Adjust x,y coordinates to match photo
    ]
}
```

### Step 4: Reload
```bash
docker compose restart
```

## Current Functionality

Even with the SVG placeholder, you get:
- ✅ Visual board representation
- ✅ Pin position indicators
- ✅ Chip log overlay
- ✅ Interactive pin controls
- ✅ All features work identically

## Tips for Creating Custom Board Images

### Option 1: Use Photo
1. Take clear, well-lit photo of board
2. Crop to just the board
3. Resize to ~300-400px width
4. Save as PNG

### Option 2: Use Datasheet
1. Get board layout from manufacturer docs
2. Screenshot or export as PNG
3. Clean up in image editor

### Option 3: Keep SVG
- Already works
- Scales perfectly
- Small file size
- No additional files needed

## Troubleshooting

**Image not showing?**
```bash
# Check file exists
ls -lh app/static/images/boards/

# Check permissions
chmod 644 app/static/images/boards/*

# Check browser console (F12)
# Look for 404 errors on image load
```

**Wrong position?**
- Open browser dev tools (F12)
- Inspect the board image
- Use element inspector to measure pixel coordinates
- Update board-configs.js accordingly

**Pins not aligned?**
- Overlay a semi-transparent grid in image editor
- Mark pin centers
- Record x,y coordinates
- Update pin array in board-configs.js

## Example Workflow

```bash
# 1. Save image from chat
# (Manual step - right-click save)

# 2. Move to correct location
mv ~/Downloads/esp32-board.png \
   app/static/images/boards/esp32-wroom-32.png

# 3. Verify
file app/static/images/boards/esp32-wroom-32.png

# 4. Restart
docker compose restart

# 5. Test
# Open modal - should now show photo instead of SVG
```

## SVG vs PNG Comparison

| Feature | SVG (Current) | PNG (Photo) |
|---------|---------------|-------------|
| Quality | Perfect at any size | Fixed resolution |
| File Size | ~4KB | ~200-500KB |
| Realism | Schematic/diagram | Actual hardware |
| Load Speed | Instant | Network dependent |
| Customization | Easy to edit | Need image editor |

**Recommendation:** Keep SVG for development, add PNG for production if desired.
