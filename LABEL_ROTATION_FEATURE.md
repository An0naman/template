# Label Rotation Feature

## Overview
Each label size now supports two orientations: **Portrait (0°)** and **Landscape (90°)**, with independent settings for each orientation.

## How It Works

### Portrait vs Landscape
- **Portrait (0°)**: Standard orientation (e.g., 60mm wide × 30mm tall)
- **Landscape (90°)**: Rotated dimensions (e.g., 30mm wide × 60mm tall)

### Key Concept
When you select "Landscape (90° Rotation)", the label **dimensions are swapped** to create a landscape layout:
- A 60×30mm label becomes 30×60mm (narrow and tall)
- A 50×14mm label becomes 14×50mm (very narrow and tall)

The content is laid out normally for the new dimensions - text is upright and readable, just in a different aspect ratio.

## Configuration

### Settings Page
1. **Select Printer Type**: Choose your printer (8 Labels, 14 Labels, B1, or D110)
2. **Select Label Size**: Choose the label dimensions
3. **Select Orientation**: Choose Portrait (0°) or Landscape (90°)
4. **Configure Settings**: Each size+orientation combo has independent settings:
   - Font sizes
   - Border styles
   - QR code options
   - QR code position

### Example Use Cases

**60×30mm Niimbot B1 Label:**
- **Portrait (60mm wide × 30mm tall)**:
  - Good for: Product labels with QR codes
  - Settings: Medium fonts, QR on right side
  
- **Landscape (30mm wide × 60mm tall)**:
  - Good for: Vertical labels on narrow products
  - Settings: Larger fonts (more vertical space), QR on top

**50×14mm Niimbot D110 Label:**
- **Portrait (50mm wide × 14mm tall)**:
  - Good for: Cable labels, thin horizontal labels
  - Settings: Small fonts, no QR code (too short)
  
- **Landscape (14mm wide × 50mm tall)**:
  - Good for: Vertical identification tags
  - Settings: Small fonts, QR code on top (now there's room!)

## Database Storage

Settings are stored with rotation suffix:
- **Portrait**: `label_60x30mm_font_size` (no suffix)
- **Landscape**: `label_60x30mm_r90_font_size` (with `_r90` suffix)

Example database keys for 60×30mm:
```
Portrait (0°):
- label_60x30mm_font_size = 8
- label_60x30mm_title_font_size = 12
- label_60x30mm_border_style = simple
- label_60x30mm_qr_position = right

Landscape (90°):
- label_60x30mm_r90_font_size = 10
- label_60x30mm_r90_title_font_size = 14
- label_60x30mm_r90_border_style = simple
- label_60x30mm_r90_qr_position = top-right
```

## Live Preview

The preview automatically:
1. **Swaps dimensions** for landscape orientation
2. **Scales down** if the label is too large for the preview area
3. **Shows orientation indicator** ("📐 Landscape (90°)") below the preview
4. **Updates in real-time** as you change settings

### Preview Behavior
- Portrait 60×30mm: Shows as wider rectangle
- Landscape 60×30mm: Shows as taller rectangle (30mm wide × 60mm tall)
- Content is always upright and readable

## Default Settings

### Portrait Defaults (0°)
- Optimized for horizontal labels
- QR codes typically on right or center-right
- Standard font sizes for the label dimensions

### Landscape Defaults (90°)
- Optimized for vertical labels
- QR codes typically on top-right (more vertical space)
- Slightly larger fonts (utilizing the increased height)

## Printing Workflow

When printing a label:
1. System checks for size-specific settings with rotation
2. Falls back to non-rotated settings if rotation settings don't exist
3. Falls back to default settings if size-specific settings don't exist

**Priority order:**
1. `label_60x30mm_r90_*` (size + rotation)
2. `label_60x30mm_*` (size only)
3. `label_*` (default)

## Visual Comparison

### 60×30mm Examples

**Portrait (0°) - 60mm wide × 30mm tall:**
```
┌───────────────────────────────────────────────┐
│ Product Name                          ▪▪▪▪▪▪  │
│ Description text here                 ▪▪▪▪▪▪  │
│ 2025-10-24                            ▪▪QR▪▪  │
└───────────────────────────────────────────────┘
     Wide and short - QR on right
```

**Landscape (90°) - 30mm wide × 60mm tall:**
```
┌─────────────────────────┐
│        ▪▪▪▪▪▪▪▪▪▪▪      │
│        ▪▪▪QR▪▪▪▪▪      │
│        ▪▪▪▪▪▪▪▪▪▪▪      │
│                         │
│    Product Name         │
│                         │
│    Description          │
│    text here            │
│                         │
│    2025-10-24           │
└─────────────────────────┘
  Narrow and tall - QR on top
```

### 50×14mm Examples

**Portrait (0°) - 50mm wide × 14mm tall:**
```
┌──────────────────────────────────────┐
│ Product Name - Date: 2025-10-24      │
└──────────────────────────────────────┘
  Very wide and thin - no room for QR
```

**Landscape (90°) - 14mm wide × 50mm tall:**
```
┌───────────┐
│  ▪▪▪▪▪▪▪  │
│  ▪▪QR▪▪▪  │
│  ▪▪▪▪▪▪▪  │
│           │
│  Product  │
│   Name    │
│           │
│   Date    │
│ 2025-10-  │
│    24     │
└───────────┘
  Very thin and tall - QR fits on top!
```

## Benefits

### 1. **Flexibility**
- Same label stock can be used in different orientations
- Optimize layout based on product shape
- Vertical labels for narrow items, horizontal for wide items

### 2. **Space Optimization**
- Landscape orientation on narrow labels provides more vertical space
- Better for QR codes on thin labels
- More room for multi-line text

### 3. **Independent Settings**
- Different font sizes for each orientation
- Different QR positions
- Different border styles
- Optimized for each use case

### 4. **Easy Switching**
- Change orientation with one click
- Settings automatically load
- Preview updates instantly

## Tips & Best Practices

### When to Use Portrait
- Wide products (bottles, boxes)
- Horizontal surfaces
- When width > height is natural
- Standard address labels

### When to Use Landscape  
- Narrow products (cables, pens, tubes)
- Vertical surfaces
- When height > width is natural
- Vertical identification tags

### Font Size Guidelines
- **Portrait narrow labels** (e.g., 50×14mm): Use smaller fonts (7-8pt)
- **Landscape narrow labels** (e.g., 14×50mm): Can use larger fonts (9-10pt) due to vertical space
- **Always test print** to verify readability

### QR Code Positioning
- **Portrait wide labels**: QR on right or center-right works well
- **Landscape tall labels**: QR on top-right or top-left to preserve text space below
- **Very small labels**: Disable QR codes in one or both orientations

## Troubleshooting

### Preview looks wrong
- Check that correct orientation is selected
- Verify label size matches your actual labels
- Preview automatically scales - actual print will be correct size

### Text too small/large after rotation
- Adjust font sizes independently for each orientation
- Portrait and landscape have separate font settings
- Test print and adjust as needed

### QR code in wrong position
- Each orientation has independent QR position setting
- Portrait might use "right", landscape might use "top-right"
- Configure each orientation separately

## Future Enhancements

Possible improvements:
- 180° and 270° rotation options
- Automatic font size suggestions based on orientation
- Rotation preview on entry detail page
- Bulk rotation for multiple labels
- Template presets for common orientations
