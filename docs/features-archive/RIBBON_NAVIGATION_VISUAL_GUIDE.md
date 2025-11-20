# Ribbon Navigation - Visual Guide

## Desktop View
```
┌────────────────────────────────────────────────────────────────────────┐
│  [Logo] AppName  │  ← Back  │  Dashboard  │  Entries  │  Settings  │  About  │
│                                    ═══════                                  │
└────────────────────────────────────────────────────────────────────────┘
```

## Tablet View (≤992px)
```
┌──────────────────────────────────────────────────────────────────┐
│  [Logo] AppName │ ← Back │ Dashboard │ Entries │ Settings │ About │
│                             ════════                              │
└──────────────────────────────────────────────────────────────────┘
```

## Mobile View (≤768px) - Icons Only
```
┌────────────────────────────────────────────────────┐
│  [Logo] AppName │ ← │ 📊 │ 📋 │ ⚙️ │ ℹ️ │
│                      ══                            │
└────────────────────────────────────────────────────┘
```

## Small Mobile (≤576px) - Wrapped Layout
```
┌──────────────────────────────┐
│  [Logo]              ℹ️       │
├──────────────────────────────┤
│  ←  │  📊  │  📋  │  ⚙️  │
│       ══                     │
└──────────────────────────────┘
```

## Button States

### Normal State
```css
Background: rgba(255, 255, 255, 0.15)
Border: rgba(255, 255, 255, 0.2)
Color: white
```

### Hover State
```css
Background: rgba(255, 255, 255, 0.25)
Border: rgba(255, 255, 255, 0.3)
Transform: translateY(-1px)
Color: white
```

### Active State (Current Page)
```css
Background: rgba(255, 255, 255, 0.3)
Border: rgba(255, 255, 255, 0.4)
Font-weight: 600
Bottom Indicator: White 3px line
```

### Disabled State (Back Button)
```css
Opacity: 0.4
Cursor: not-allowed
Pointer-events: none
```

## Icons Used

| Button      | Icon Class         | Unicode |
|-------------|-------------------|---------|
| Back        | fa-arrow-left     | ←       |
| Dashboard   | fa-chart-line     | 📊      |
| Entries     | fa-list           | 📋      |
| Settings    | fa-cog            | ⚙️      |
| About       | fa-info-circle    | ℹ️      |

## Color Scheme

### Light Mode
- Gradient: Primary color → Primary hover color
- Text: White
- Border: rgba(255, 255, 255, 0.1)
- Shadow: rgba(0, 0, 0, 0.1)

### Dark Mode
- Gradient: Primary color → Primary hover color (darker)
- Text: White
- Border: rgba(255, 255, 255, 0.05)
- Shadow: rgba(0, 0, 0, 0.3)
- Buttons: Slightly more opaque

## Spacing

### Desktop
- Container padding: 1.5rem
- Button gap: 0.5rem
- Logo-to-title gap: 0.75rem
- Navigation margin: 1rem

### Mobile
- Container padding: 0.75rem
- Button gap: 0.25rem
- Logo-to-title gap: 0.25rem
- Navigation margin: 0.25rem

## Example Screenshots

### Navigation in Action

**Page: Dashboard (Active)**
```
┌────────────────────────────────────────────────────────────────────┐
│  [Logo] MyApp  │  ← Back  │  Dashboard  │  Entries  │  Settings  │  About  │
│                              ═════════                                  │
└────────────────────────────────────────────────────────────────────┘
                                  ↑
                           Active indicator
```

**Page: Entry Detail (Entries Active)**
```
┌────────────────────────────────────────────────────────────────────┐
│  [Logo] MyApp  │  ← Back  │  Dashboard  │  Entries  │  Settings  │  About  │
│                                           ════════                      │
└────────────────────────────────────────────────────────────────────┘
                                              ↑
                                  Parent section highlighted
```

**Page: Dashboard (Back Button Disabled)**
```
┌────────────────────────────────────────────────────────────────────┐
│  [Logo] MyApp  │  ← Back  │  Dashboard  │  Entries  │  Settings  │  About  │
│                   (grayed)   ═════════                                  │
└────────────────────────────────────────────────────────────────────┘
                       ↑
                  Disabled state
```

## Interaction Flow

### Scenario 1: Basic Navigation
```
1. User lands on Dashboard
   → Dashboard highlighted, Back disabled
   
2. User clicks "Entries"
   → Navigates to Entries page
   → Entries highlighted, Back enabled
   
3. User clicks "Back"
   → Returns to Dashboard
   → Dashboard highlighted
```

### Scenario 2: Deep Navigation
```
1. Dashboard → Entries → Entry #123 → Back → Back
   
   Dashboard (Back: OFF)
      ↓ click Entries
   Entries (Back: ON)
      ↓ click entry
   Entry #123 (Back: ON, Entries highlighted)
      ↓ click Back
   Entries (Back: ON)
      ↓ click Back
   Dashboard (Back: OFF)
```

### Scenario 3: Direct Navigation
```
1. Dashboard (Back: OFF)
      ↓ click Settings
2. Settings (Back: ON)
      ↓ click Entries
3. Entries (Back: ON)
   
History: [Dashboard, Settings, Entries]
Position: 2
```

## Animation Timing

```css
Transitions:
- All properties: 0.2s ease
- Transform on hover: 0.2s ease
- Active state indicator: instant

Button Hover:
- Background opacity: 0.15 → 0.25 (100ms fade)
- Transform: 0 → -1px (150ms ease-out)
```

## Accessibility Labels

```html
Back Button:
- Default title: "Go back to previous page"
- Disabled title: "No previous page"

Dashboard Button:
- title: "Dashboard"
- ARIA accessible via text

Entries Button:
- title: "Entries"
- ARIA accessible via text

Settings Button:
- title: "Settings"
- ARIA accessible via text
```

## Browser Storage

```javascript
sessionStorage keys:
- 'ribbon_nav_history': JSON array of page objects
- 'ribbon_nav_position': Integer (current index)

Example:
{
  "ribbon_nav_history": "[
    {\"url\":\"/dashboard\",\"title\":\"Dashboard\",\"timestamp\":1699900000000},
    {\"url\":\"/entries\",\"title\":\"Entries\",\"timestamp\":1699900005000}
  ]",
  "ribbon_nav_position": "1"
}
```

## Testing Checklist

### Visual Tests
- [ ] Dashboard button highlights on dashboard page
- [ ] Entries button highlights on entries/entry pages
- [ ] Settings button highlights on settings pages
- [ ] Back button is grayed out on first page
- [ ] Back button is active after navigation
- [ ] Active page has underline indicator
- [ ] Buttons have hover effects
- [ ] Mobile view shows icons only
- [ ] Small mobile view wraps correctly

### Functional Tests
- [ ] Click Dashboard → navigates to dashboard
- [ ] Click Entries → navigates to entries
- [ ] Click Settings → navigates to settings
- [ ] Click Back → returns to previous page
- [ ] Back button disabled when no history
- [ ] History persists on page refresh
- [ ] History clears on new browser session
- [ ] No duplicate consecutive entries in history

### Responsive Tests
- [ ] Desktop view (>992px) - all elements visible
- [ ] Tablet view (768-992px) - compact layout
- [ ] Mobile view (576-768px) - icon-only buttons
- [ ] Small mobile (<576px) - wrapped layout

### Browser Tests
- [ ] Chrome/Edge - full functionality
- [ ] Firefox - full functionality
- [ ] Safari - full functionality
- [ ] Mobile browsers - touch-friendly
