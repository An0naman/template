# Logo Feature and Adaptive Text Layout

## Overview
Labels now support both **QR codes** and **project logos** with intelligent text layout that adapts to both elements automatically.

## New Features

### 1. Logo Inclusion
- **Toggle**: Enable/disable logo per label size and orientation
- **Position Options**:
  - Top Left Corner
  - Top Right Corner
  - Left Side
  - Bottom Left Corner

### 2. Adaptive Text Layout
ALL text (title, description, details) now automatically adjusts based on:
- **QR code position** (if enabled)
- **Logo position** (if enabled)
- **Label dimensions** (width × height)
- **Orientation** (portrait vs landscape)

## How Adaptive Layout Works

### Text Width Calculation
The system calculates available text width by:
1. Starting with full label width minus margins
2. Subtracting QR code width (if on right/left)
3. Subtracting logo width (if on left/top-left)
4. Accounting for padding between elements

### Text Starting Position
- **Normal**: Starts at left margin
- **With left-side logo**: Starts after logo + padding
- **With left-side QR**: Starts after QR + padding
- **With both**: Accounts for both elements

## Configuration Examples

### Example 1: QR Right + Logo Top-Left
```
┌─────────────────────────────┐
│ [LOGO]                 [QR] │
│                        [  ] │
│ Sample Product Title   [  ] │
│ Entry #123                  │
│ Description text            │
└─────────────────────────────┘
```
- Logo: Top-left corner
- QR: Right side
- Text: Starts after logo, ends before QR
- **Text width**: Reduced on both sides

### Example 2: QR Top-Right + Logo Left Side
```
┌─────────────────────────────┐
│        [LOGO]          [QR] │
│                        [  ] │
│        Sample Product       │
│        Title                │
│        Entry #123           │
│        Description          │
└─────────────────────────────┘
```
- Logo: Left side (vertical center)
- QR: Top-right corner
- Text: Starts after logo, uses full width to right
- **Text width**: Reduced on left only

### Example 3: Logo Only (No QR)
```
┌─────────────────────────────┐
│ [LOGO]                      │
│        Sample Product Title │
│        Entry #123           │
│        Description text     │
└─────────────────────────────┘
```
- Logo: Top-left corner
- QR: Disabled
- Text: Starts after logo
- **Text width**: Reduced on left only

### Example 4: QR Only (No Logo)
```
┌─────────────────────────────┐
│ Sample Product Title   [QR] │
│ Entry #123 - Product   [  ] │
│ Sample description     [  ] │
└─────────────────────────────┘
```
- Logo: Disabled
- QR: Right side
- Text: Uses left portion
- **Text width**: Reduced on right only

## Landscape Orientation with Logo

### 60×30mm Landscape (30mm wide × 60mm tall)
```
┌───────────┐
│  [LOGO]   │
│           │
│   [QR ]   │
│   [   ]   │
│           │
│  Sample   │
│  Product  │
│  Title    │
│           │
│  Entry    │
│  #123     │
│           │
│  Desc..   │
└───────────┘
```
- Logo: Top-left (above QR)
- QR: Top-right or top area
- Text: Below both, uses full narrow width
- **Vertical stacking** of all elements

## Logo Sizing

### Automatic Sizing
Logo size is calculated as:
- **Maximum**: 60 pixels
- **Constrained by**: 30% of height OR 20% of width
- **Smaller than**: QR code (to maintain hierarchy)

### Size Examples
- 60×30mm label: ~50-60px logo
- 30×15mm label: ~40-45px logo  
- 30×60mm rotated: ~50-60px logo (more vertical space)

## Database Storage

Logo settings stored with same pattern as other settings:

**Portrait (0°):**
```
label_60x30mm_include_logo = false
label_60x30mm_logo_position = top-left
```

**Landscape (90°):**
```
label_60x30mm_r90_include_logo = false
label_60x30mm_r90_logo_position = top-left
```

## Use Cases

### When to Enable Logo

**Good for:**
- Brand recognition on products
- Professional appearance
- Corporate labeling
- Retail products
- Large labels with space (60×30mm, 40×24mm)

**Not recommended for:**
- Very small labels (30×12mm, 40×12mm)
- Labels with lots of text
- Labels that need maximum text space
- Simple organizational labels

### Logo Position Guidelines

**Top-Left:**
- Most common
- Doesn't interfere with QR on right
- Professional appearance
- Good for portrait and landscape

**Top-Right:**
- Use when QR is on left or bottom
- Alternative branding position
- Less common but effective

**Left Side:**
- Vertical labels benefit from this
- Centers logo on left edge
- Text flows to the right
- Good for landscape orientation

**Bottom-Left:**
- Least intrusive to title/content
- Good when top area is crowded
- Alternative positioning

## Preview Behavior

The live preview shows:
- ✅ Green bordered box for logo ("LOGO" text)
- ✅ Gray bordered box for QR code ("QR" text)
- ✅ Text automatically wraps and positions around both
- ✅ Real-time updates as you change settings
- ✅ Accurate representation of final layout

## Configuration Workflow

1. **Select printer and label size**
2. **Choose orientation** (Portrait/Landscape)
3. **Enable/disable QR code**
   - Set QR size and position
4. **Enable/disable logo**
   - Set logo position
5. **Adjust font sizes** for text
6. **Watch preview** update in real-time
7. **Save settings** for this size+orientation

## Best Practices

### Logo + QR Combination

**Recommended Layouts:**
- Logo: Top-left + QR: Right → Clean separation
- Logo: Left + QR: Top-right → Balanced
- Logo: Top-left + QR: Bottom-right → Diagonal balance
- Logo: Bottom-left + QR: Top-right → Maximum separation

**Avoid:**
- Logo and QR both on same side (crowds one area)
- Both at top (pushes text too low)
- Too many elements on small labels

### Text Optimization

**When using logo + QR:**
- Use **slightly smaller fonts** to fit text
- Keep **titles concise** (2-3 words)
- Use **shorter descriptions**
- Test with **realistic content length**

**Landscape with logo + QR:**
- Stack elements vertically (logo top, QR below, text below)
- Use **top positions** for logo and QR
- Text fills **remaining vertical space**
- Expect **more text wrapping**

## Technical Details

### Text Width Formula
```javascript
baseWidth = labelWidth - (margins × 2) - padding;

if (qr_on_right) {
    baseWidth -= qrSize + padding;
}

if (logo_on_left || logo_on_top_left) {
    baseWidth -= logoSize + padding;
    textStartX = margin + logoSize + padding;
}

if (qr_on_right && logo_on_left) {
    baseWidth = labelWidth - qrSize - logoSize - margins - padding;
}
```

### Element Priority
1. **Borders** drawn first (background)
2. **Logo** drawn (if enabled)
3. **QR code** drawn (if enabled)
4. **Text** drawn (wraps around logo/QR)
5. **Date** drawn at bottom

## Future Enhancements

Potential improvements:
- Upload custom logo image
- Logo size customization (small/medium/large)
- More logo positions (center, right side)
- Logo opacity/transparency settings
- Logo rotation options
- Multiple logo support
- Logo + text combination in header

## Summary

✅ **Logo feature added** with 4 position options
✅ **All text is adaptive** to both QR and logo
✅ **Independent settings** per size and orientation
✅ **Live preview** shows exact layout
✅ **Smart positioning** prevents overlaps
✅ **Flexible combinations** of logo + QR + text

The system now intelligently manages label real estate, ensuring text, QR codes, and logos all fit harmoniously! 🎨
