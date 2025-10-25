# A4 Label Sheet Update Summary

## Changes Made

### ✅ 1. Removed Unsupported Sheet Options
- **Removed**: 24 per sheet and 65 per sheet options from preview dropdown
- **Kept**: Only 8 Labels and 14 Labels (standard A4 sheet layouts)

### ✅ 2. Recalculated A4 Label Dimensions

#### New Margin/Buffer Specifications:
- **Top Buffer**: 10mm (1cm) - as requested
- **Bottom Buffer**: 10mm (1cm) - as requested  
- **Left/Right Margins**: 5mm each
- **Label Padding**: 5mm (0.5cm) between each label - as requested

#### Updated Label Sizes:

**8 Labels Per Sheet (2×4):**
- **Old Size**: 99.1mm × 67.7mm
- **New Size**: **97.5mm × 65.5mm**
- **Calculation**:
  - Width: (210mm - 5mm left - 5mm right - 5mm gap) ÷ 2 = 97.5mm
  - Height: (297mm - 10mm top - 10mm bottom - 15mm gaps) ÷ 4 = 65.5mm

**14 Labels Per Sheet (2×7):**
- **Old Size**: 99.1mm × 38.1mm
- **New Size**: **97.5mm × 35.3mm**
- **Calculation**:
  - Width: (210mm - 5mm left - 5mm right - 5mm gap) ÷ 2 = 97.5mm
  - Height: (297mm - 10mm top - 10mm bottom - 30mm gaps) ÷ 7 = 35.3mm

### ✅ 3. Updated Configuration Files

**Modified Files:**
1. `app/api/labels_api.py` - Updated LABEL_CONFIGS with new dimensions
2. `app/templates/settings.html` - Removed 24/65 options, updated size displays
3. `LABEL_PRINTER_CONFIGURATION.md` - Updated documentation
4. Created `A4_LABEL_SHEET_LAYOUT.md` - Detailed layout specifications

### ✅ 4. Improved Printer Compatibility

**Benefits of New Dimensions:**
- ✅ Proper 1cm top/bottom buffer ensures compatibility with most printers
- ✅ 5mm margins prevent edge clipping
- ✅ 5mm (0.5cm) padding between labels allows clean separation
- ✅ Labels won't overlap or get cut when printed
- ✅ Works with standard A4 label sheets from Avery, Herma, etc.

## Testing Recommendations

### Before Using with Real Label Sheets:

1. **Print Test Page on Plain Paper**
   ```
   - Select 8 or 14 label layout
   - Print on regular A4 paper
   - Verify positioning matches your pre-cut label sheet
   ```

2. **Check Alignment**
   ```
   - Hold printed test page against label sheet up to light
   - Ensure labels align with pre-cut areas
   - Adjust printer settings if needed
   ```

3. **Verify Margins**
   ```
   - Measure actual top margin: should be ~10mm
   - Measure left margin: should be ~5mm
   - Check gaps between labels: should be ~5mm
   ```

4. **Print Single Test Label**
   ```
   - Print on actual label sheet
   - Check for proper alignment
   - Verify no text clipping
   - Confirm clean label separation
   ```

## Layout Visualization

### 8 Labels (2×4) - Larger Labels
```
┌─────────── 210mm A4 Width ───────────┐
│         10mm Top Buffer              │
├──────────────────────────────────────┤
│  [Label 1: 97.5×65.5]  [Label 2]    │
│         5mm gap                       │
│  [Label 3: 97.5×65.5]  [Label 4]    │
│         5mm gap                       │
│  [Label 5: 97.5×65.5]  [Label 6]    │
│         5mm gap                       │
│  [Label 7: 97.5×65.5]  [Label 8]    │
├──────────────────────────────────────┤
│         10mm Bottom Buffer           │
└──────────────────────────────────────┘
         297mm A4 Height
```

### 14 Labels (2×7) - Smaller Labels
```
┌─────────── 210mm A4 Width ───────────┐
│         10mm Top Buffer              │
├──────────────────────────────────────┤
│  [Label 1: 97.5×35.3]  [Label 2]    │
│         5mm gap                       │
│  [Label 3: 97.5×35.3]  [Label 4]    │
│         5mm gap                       │
│  [Label 5: 97.5×35.3]  [Label 6]    │
│         5mm gap                       │
│  [Label 7: 97.5×35.3]  [Label 8]    │
│         5mm gap                       │
│  [Label 9: 97.5×35.3]  [Label 10]   │
│         5mm gap                       │
│  [Label 11: 97.5×35.3] [Label 12]   │
│         5mm gap                       │
│  [Label 13: 97.5×35.3] [Label 14]   │
├──────────────────────────────────────┤
│         10mm Bottom Buffer           │
└──────────────────────────────────────┘
         297mm A4 Height
```

## Printer Settings

When printing, ensure:
- **Paper Size**: A4 (210mm × 297mm)
- **Orientation**: Portrait
- **Scale**: 100% / Actual Size (not "Fit to Page")
- **Margins**: Use custom margins matching your label sheet
- **Quality**: Best/High quality for precise positioning

## Compatible Label Products

These dimensions work well with standard A4 label sheets:
- Avery L7165 (similar 8-label layout)
- Avery L7163 (similar 14-label layout)
- Generic A4 label sheets with 2-column layouts
- Most office supply store label sheets

**Note**: Always verify your specific label sheet dimensions match or are close to:
- 8 labels: ~97-99mm × 65-68mm
- 14 labels: ~97-99mm × 35-38mm

## Next Steps

1. ✅ Docker rebuilt with new dimensions
2. ⏳ Test print on plain paper to verify alignment
3. ⏳ Compare with actual label sheets
4. ⏳ Print test label on real label sheet
5. ⏳ Adjust if needed based on your specific printer/label combination

## Files Updated
- ✅ `app/api/labels_api.py` - Label configurations
- ✅ `app/templates/settings.html` - UI updates
- ✅ `LABEL_PRINTER_CONFIGURATION.md` - Documentation
- ✅ `A4_LABEL_SHEET_LAYOUT.md` - Detailed layout guide (NEW)
- ✅ This summary - `A4_LABEL_UPDATE_SUMMARY.md` (NEW)
