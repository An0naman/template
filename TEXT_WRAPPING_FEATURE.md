# Text Wrapping Feature for Label Previews

## Overview
The label preview now includes intelligent text wrapping that automatically adjusts based on label dimensions and QR code placement. This is especially important for landscape (90°) orientations where labels are narrower.

## How Text Wrapping Works

### Smart Width Calculation
The preview calculates available text width based on:
1. **Label dimensions** (width - margins)
2. **QR code position** (if QR is on right, text width is reduced)
3. **QR code size** (larger QR codes = less text space)

### Wrapping Algorithm
- Breaks text at word boundaries (doesn't cut words in half)
- Measures each word to determine if it fits on the current line
- Automatically creates new lines when text exceeds available width
- Maintains consistent line height for readability

## Benefits for Different Orientations

### Portrait (0°) - Wider Labels
**Example: 60×30mm (60mm wide × 30mm tall)**
- More horizontal space for text
- Less wrapping needed
- QR code on right still leaves room for ~40-45mm of text width
- Typical use: 1-2 lines for title, 1-2 lines for description

### Landscape (90°) - Narrower Labels  
**Example: 60×30mm rotated → 30×60mm (30mm wide × 60mm tall)**
- **Much narrower** - only 30mm wide
- **More wrapping needed** - text breaks more frequently
- **More vertical space** - can accommodate many more lines
- QR code on top doesn't reduce text width
- Typical use: 3-4 lines for title, 4-5 lines for description

## Preview Examples

### 60×30mm Portrait (Wide)
```
┌───────────────────────────────────────────────┐
│ Sample Product Title                  ▪▪▪▪▪▪  │
│ Entry #123 - Type: Product            ▪▪QR▪▪  │
│ Sample description text that wraps    ▪▪▪▪▪▪  │
│ 2025-10-24                                    │
└───────────────────────────────────────────────┘
   Wide format - minimal wrapping
```

### 60×30mm Landscape (Narrow)
```
┌─────────────────────────┐
│      ▪▪▪▪▪▪▪▪▪▪▪        │
│      ▪▪▪QR▪▪▪▪▪        │
│      ▪▪▪▪▪▪▪▪▪▪▪        │
│                         │
│  Sample Product         │
│  Title                  │
│                         │
│  Entry #123 -           │
│  Type: Product          │
│                         │
│  Sample                 │
│  description            │
│  text that wraps        │
│                         │
│  2025-10-24             │
└─────────────────────────┘
   Narrow format - extensive wrapping
```

### 50×14mm Portrait (Very Wide, Very Short)
```
┌──────────────────────────────────────────────┐
│ Sample Product Title - Entry #123 - Product │
│ Sample description text - 2025-10-24        │
└──────────────────────────────────────────────┘
   Wide but short - long lines, minimal wrapping
```

### 50×14mm Landscape (Very Narrow, Very Tall)
```
┌─────────┐
│ ▪▪▪▪▪▪▪ │
│ ▪▪QR▪▪▪ │
│ ▪▪▪▪▪▪▪ │
│         │
│ Sample  │
│ Product │
│ Title   │
│         │
│ Entry   │
│ #123 -  │
│ Type:   │
│ Product │
│         │
│ Sample  │
│ desc..  │
│ text    │
│ that    │
│ wraps   │
│         │
│ 2025-   │
│ 10-24   │
└─────────┘
   Very narrow - each word may be on own line
```

## Technical Implementation

### Text Width Calculation
```javascript
// Base width (label width minus margins)
let textMaxWidth = width - (margin * 2) - 10;

// If QR code is on the right side, reduce text width
if (qrPosition === 'right' || qrPosition === 'top-right' || qrPosition === 'bottom-right') {
    textMaxWidth = width - qrPixels - (margin * 2) - 20;
}
```

### Wrap Function
```javascript
function wrapText(context, text, x, y, maxWidth, lineHeight) {
    const words = text.split(' ');
    let line = '';
    let lines = [];
    
    // Test each word to see if it fits
    for (let n = 0; n < words.length; n++) {
        const testLine = line + words[n] + ' ';
        const metrics = context.measureText(testLine);
        
        if (metrics.width > maxWidth && n > 0) {
            lines.push(line);  // Current line is full
            line = words[n] + ' ';  // Start new line
        } else {
            line = testLine;  // Add word to current line
        }
    }
    lines.push(line);  // Add last line
    
    // Draw all lines
    for (let i = 0; i < lines.length; i++) {
        context.fillText(lines[i], x, y + (i * lineHeight));
    }
    
    return lines.length * lineHeight;  // Total height used
}
```

### Line Height
- **Title**: `fontSize + 4px` (e.g., 14pt title = 18px line height)
- **Body text**: `fontSize + 4px` (e.g., 10pt body = 14px line height)
- Provides comfortable spacing between lines

## QR Code Position Impact

### QR on Right/Center-Right
- **Reduces horizontal text space**
- Text wraps more aggressively
- Good for portrait orientations with enough width

### QR on Top/Bottom
- **Doesn't reduce horizontal text space**
- Text can use full width
- **Recommended for landscape orientations**
- Reduces vertical space instead

### QR on Left
- Similar to right-side QR
- Less common, but text adjusts accordingly

## Font Size Recommendations by Orientation

### Portrait (Wide) Orientations
- **60×30mm**: 8-10pt body, 12-14pt title
- **50×14mm**: 7-8pt body, 10-11pt title
- **40×12mm**: 6-7pt body, 9-10pt title

### Landscape (Narrow) Orientations
- **30×60mm** (60×30 rotated): 9-11pt body, 13-15pt title
  - Narrower, so slightly smaller fonts work better
  - More vertical space allows more lines
  
- **14×50mm** (50×14 rotated): 7-9pt body, 10-12pt title
  - Very narrow, keep fonts moderate
  - Lots of vertical space for wrapping
  
- **12×40mm** (40×12 rotated): 6-8pt body, 9-11pt title
  - Extremely narrow
  - Smaller fonts prevent single-word-per-line

## Best Practices

### 1. Test Both Orientations
- Preview both portrait and landscape
- Adjust font sizes for each independently
- Verify text wraps nicely in both modes

### 2. QR Code Placement
- **Portrait**: QR on right or center-right
- **Landscape**: QR on top-right or top-left
  - Preserves full text width
  - Uses vertical space efficiently

### 3. Content Length
- **Shorter titles** wrap better on narrow labels
- **Keep descriptions concise** for landscape orientations
- Test with realistic content length

### 4. Font Size Balance
- **Landscape labels**: Can use slightly larger fonts
  - More vertical space
  - Wrapping is expected
  
- **Portrait labels**: Keep fonts moderate
  - Limited vertical space
  - Want to minimize wrapping

## Preview Accuracy

The preview provides a realistic representation of:
- ✅ Text wrapping behavior
- ✅ Line breaks and spacing
- ✅ QR code space reservation
- ✅ Available text area
- ✅ Font size appearance

**Note**: Actual printed labels may have slight variations based on:
- Printer resolution
- Font rendering
- Paper/label material
- Thermal printer characteristics (for Niimbot)

## Future Enhancements

Potential improvements:
- Ellipsis (…) for text that doesn't fit vertically
- Character wrapping for very long words
- Custom line height settings
- Adjustable text alignment (left, center, right)
- Multi-column text layout for very wide labels
- Preview with actual entry data instead of dummy text
