# Battery Calibration - Simple Guide

## What You Need to Do (Simple!)

1. **Check your device's battery reading** in the dashboard (e.g., shows "1.8V")
2. **Measure actual voltage** with your multimeter (e.g., reads "4.03V")
3. **Enter the multimeter reading** in "Actual Voltage" field
4. **Click "Auto-Calibrate"** button
5. **Done!** The system calculates everything automatically

## How It Works (Behind the Scenes)

### The Problem
Your device uses a **voltage divider** circuit to read battery voltage:

```
Battery (4.03V actual)
   |
  [R1] ← Unknown resistor
   |
ADC Pin (reads scaled voltage)
   |
  [R2] ← Unknown resistor
   |
  GND
```

The firmware formula is: `Vbat = Vadc × (R1 + R2) / R2`

**But we don't know the exact R1 and R2 values!**

### The Solution (Auto-Calibration)

When you click "Auto-Calibrate":

1. **System reads**: Device reports 1.8V (wrong!)
2. **You measured**: 4.03V (correct!)
3. **System calculates**: Correction factor = 4.03 / 1.8 = **2.239x**
4. **System adjusts**: Changes the R1/R2 ratio to apply this correction
   - Keeps R2 = 100kΩ (standard)
   - Calculates R1 = 123,900Ω (to get 2.239x multiplier)
5. **Next time device fetches script**: It gets R1=123900, R2=100000
6. **Device now reads**: 4.03V ✓ (correct!)

### Example Calculation

```
Current reading:  1.8V (device)
Actual voltage:   4.03V (multimeter)
Correction:       4.03 / 1.8 = 2.239

Current ratio:    (100k + 100k) / 100k = 2.0
Needed ratio:     2.0 × 2.239 = 4.478

New values:       R1 = 347,800Ω, R2 = 100,000Ω
Check:            (347800 + 100000) / 100000 = 4.478 ✓
```

## Why This Is Better

### Old Way (Manual):
- Enter multimeter reading ❌
- Guess R1 value ❌
- Guess R2 value ❌
- Hope it works ❌
- Confusing! ❌

### New Way (Auto):
- Enter multimeter reading ✓
- Click "Auto-Calibrate" ✓
- Done! ✓
- Simple! ✓

## Technical Details (For Advanced Users)

### Voltage Divider Formula
```
Vout = Vin × (R2 / (R1 + R2))
Vin = Vout × ((R1 + R2) / R2)

Where:
- Vin = Battery voltage (what we want to know)
- Vout = ADC reading (what ESP32 reads)
- R1 = Top resistor (Battery → ADC)
- R2 = Bottom resistor (ADC → GND)
```

### Calibration Math
```
Given:
- Actual battery voltage (Va) from multimeter
- Current device reading (Vd) from sensor
- Current R1/R2 ratio (Rc = (R1+R2)/R2)

Calculate:
- Correction factor: Cf = Va / Vd
- New ratio needed: Rn = Rc × Cf
- New R1: R1 = (Rn × R2) - R2
```

### Why Keep R2 Constant?
- Standard value (100kΩ) is common
- Only need to adjust one resistor
- Easier to understand the correction
- R1 becomes the "tuning" parameter

## Common Board Defaults

| Board | Default R1 | Default R2 | Ratio |
|-------|-----------|-----------|-------|
| ESP32-WROOM-32 | 100kΩ | 100kΩ | 2.0x |
| FireBeetle 2 C6 | ~146kΩ | 100kΩ | 2.46x |
| Generic ESP32 | 100kΩ | 100kΩ | 2.0x |

**Note:** FireBeetle boards often have built-in voltage dividers with different ratios, which is why calibration is especially important!

## Troubleshooting

### "Device must report a battery voltage first"
**Problem:** The dashboard shows "N/A" for current reading

**Solution:**
1. Wait for device to send a reading (check every ~60 seconds)
2. Or manually trigger a battery read from the Logic Builder
3. Or use the Interactive Board Monitor to execute a battery read

### "Calibration saved but still shows wrong"
**Problem:** Saved calibration but readings unchanged

**Solution:**
1. Device needs to fetch the updated script
2. Devices check for updates every ~5 minutes
3. Or restart the device to force immediate fetch
4. Check the "Running Version" column - should update after fetch

### "Percentage still wrong"
**Problem:** Voltage is correct but percentage is off

**Solution:**
The percentage calculation uses min/max voltage ranges:
- Check your battery type (LiPo: 3.3-4.2V, Li-Ion: 3.0-4.2V)
- Adjust `min_v` and `max_v` in the battery read block
- Common ranges:
  - LiPo: 3.3V (empty) to 4.2V (full)
  - Li-Ion: 3.0V (empty) to 4.2V (full)
  - LiFePO4: 2.5V (empty) to 3.65V (full)

## What Happens Next?

After calibration:
1. ✅ Values saved to database immediately
2. ✅ Device fetches script on next check (~5 min or on restart)
3. ✅ Script has calibrated R1/R2 values injected automatically
4. ✅ Device uses new values for all future readings
5. ✅ Dashboard shows accurate voltage and percentage
6. ✅ Plotter charts show correct values

## Need Manual Control?

If you actually know your R1/R2 values (e.g., you built the circuit):
1. Expand "Advanced (Manual R1/R2)" section
2. Enter exact R1 and R2 values
3. Click "Save Manual R1/R2"
4. System uses your exact values (no auto-calculation)
