# Label Orientation Fix

## Problem
Labels are printing but the orientation is wrong - text might be sideways or upside down.

## Solution
The API now supports a `rotation` parameter to fix orientation!

## Quick Test

Run the orientation test script:
```bash
python test_label_orientation.py
```

This will print 4 test labels with different rotations (0°, 90°, -90°, 180°). See which one is correct!

## Common Rotations

| Rotation | When to Use |
|----------|-------------|
| `0` | Label loaded horizontally, print head on left |
| `90` | Label loaded vertically, print head on top (clockwise) |
| `-90` | Label loaded vertically, print head on bottom (counter-clockwise) |
| `180` | Label loaded horizontally, print head on right (upside down) |

## Using the API

### Default (current -90°)
```bash
curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
  -H "Content-Type: application/json" \
  -d '{
    "printer_address": "B1",
    "printer_model": "b1",
    "density": 3
  }'
```

### With Custom Rotation
```bash
curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
  -H "Content-Type: application/json" \
  -d '{
    "printer_address": "B1",
    "printer_model": "b1",
    "density": 3,
    "rotation": 90
  }'
```

### From JavaScript
```javascript
fetch('/api/entries/123/niimbot/print', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    printer_address: 'B1',
    printer_model: 'b1',
    density: 3,
    quantity: 1,
    rotation: 90  // Try: 0, 90, -90, or 180
  })
});
```

## How It Works

1. **Label is generated**: 384x110 pixels (50x14mm landscape)
2. **Rotation is applied**: 
   - `0` → 384x110 (no change)
   - `90` → 110x384 (portrait, clockwise)
   - `-90` → 110x384 (portrait, counter-clockwise)
   - `180` → 384x110 (landscape, flipped)
3. **Sent to printer**: In the rotated orientation

## Finding the Right Rotation

### Method 1: Test Script
```bash
python test_label_orientation.py
```
Choose "a" to test all rotations, or pick one.

### Method 2: Manual Testing
Try each rotation with a real entry:

```bash
# Test 0°
curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
  -H "Content-Type: application/json" \
  -d '{"printer_address": "B1", "printer_model": "b1", "rotation": 0}'

# Test 90°
curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
  -H "Content-Type: application/json" \
  -d '{"printer_address": "B1", "printer_model": "b1", "rotation": 90}'

# Test -90°
curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
  -H "Content-Type: application/json" \
  -d '{"printer_address": "B1", "printer_model": "b1", "rotation": -90}'

# Test 180°
curl -X POST http://localhost:5000/api/entries/1/niimbot/print \
  -H "Content-Type: application/json" \
  -d '{"printer_address": "B1", "printer_model": "b1", "rotation": 180}'
```

## Setting a Default

Once you find the right rotation, you can:

1. **Update frontend** to always use that rotation
2. **Change the default** in `app/api/labels_api.py`:
   ```python
   rotation = int(data.get('rotation', 90))  # Change -90 to your preferred default
   ```

## Label Loading Reference

```
B1 Printer with 50x14mm labels:

┌─────────────────────┐
│                     │
│    Niimbot B1       │  ← Print head
│                     │
└─────────────────────┘
        ↑
    Feed direction
    
If labels feed from bottom to top:
- Text should read normally when label exits top
- Try rotation = -90 or 90

If labels feed from left to right:
- Text should read normally when label exits right
- Try rotation = 0 or 180
```

## Troubleshooting

### Text is sideways
- Try changing rotation by 90° or -90°

### Text is upside down
- Add or subtract 180° from current rotation

### Text is mirrored
- This shouldn't happen with normal rotation
- Check if image generation is correct

## Quick Reference

| Current Result | Try This Rotation |
|----------------|-------------------|
| Text rotated left | Add 90° |
| Text rotated right | Add -90° |
| Text upside down | Add 180° |
| Text correct | Keep current! |

---

**TIP**: Save the correct rotation value in your app's settings/config so users don't have to specify it every time!
