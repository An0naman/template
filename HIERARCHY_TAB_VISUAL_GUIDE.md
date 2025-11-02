# 🌲 Hierarchy Tab - Visual Guide

## Tab Navigation

```
┌──────────────────────────────────────────────────────┐
│  Related Records                            [👁 Show Empty] │
├──────────────────────────────────────────────────────┤
│  [📋 Grouped View] [🌲 Hierarchy View] ←── New Tab! │
└──────────────────────────────────────────────────────┘
```

## Hierarchy View Display

### Example 1: Simple Parent-Child Hierarchy

```
🌲 Hierarchy View
├──────────────────────────────────────────────────────┤

▼ 📊 Project Alpha [Parent]
  │
  ├─ ▼ 📋 Feature Development [Current]
  │  │
  │  ├─ ▶ ✅ Task: Design mockups
  │  │     Status: Completed
  │  │
  │  ├─ ▶ ⏳ Task: Implement frontend
  │  │     Status: In Progress
  │  │
  │  └─ ▶ 📝 Task: Write tests
  │        Status: Not Started
  │
  └─ ▶ 📋 Documentation
       Status: In Progress
```

### Example 2: Multi-Level Hierarchy

```
▼ 🏢 Organization
  │
  ├─ ▼ 📊 Department A
  │  │
  │  ├─ ▼ 👤 Team Lead [Current]
  │  │  │
  │  │  ├─ ▶ 👤 Developer 1
  │  │  ├─ ▶ 👤 Developer 2
  │  │  └─ ▶ 👤 Developer 3
  │  │
  │  └─ ▼ 📁 Project X
  │     │
  │     ├─ ▶ 📋 Sprint 1
  │     └─ ▶ 📋 Sprint 2
  │
  └─ ▼ 📊 Department B
     └─ ▶ 👤 Manager
```

## Interactive Elements

### Node Types

#### 1. Current Entry (You are here)
```
┌─────────────────────────────────────────┐
│ ▼ 📋 Feature Development [Current] ⭐   │ ← Blue highlight
│                                         │
└─────────────────────────────────────────┘
```

#### 2. Parent Entry
```
┌─────────────────────────────────────────┐
│ ▼ 📊 Project Alpha [Parent] 📌          │ ← Cyan highlight
│                                         │
└─────────────────────────────────────────┘
```

#### 3. Regular Entry
```
┌─────────────────────────────────────────┐
│ ▶ ✅ Task: Design mockups               │ ← No highlight
│   Status: Completed                      │
└─────────────────────────────────────────┘
```

### Expand/Collapse Controls

#### Collapsed State
```
▶ 📊 Project Alpha [Parent]
  (children hidden)
```

#### Expanded State
```
▼ 📊 Project Alpha [Parent]
  ├─ 📋 Feature 1
  ├─ 📋 Feature 2
  └─ 📋 Feature 3
```

## Color Coding

### Light Mode
- **Current Entry**: Blue background (#0d6efd at 10% opacity)
- **Parent Entry**: Cyan background (#0dcaf0 at 10% opacity)
- **Hover**: Light gray background
- **Icons**: Colored by entry type

### Dark Mode
- **Current Entry**: Blue background (#0d6efd at 20% opacity)
- **Parent Entry**: Cyan background (#0dcaf0 at 15% opacity)
- **Hover**: Dark gray background
- **Icons**: Colored by entry type (adjusted for dark mode)

## Entry Components

Each tree node displays:

```
┌─────────────────────────────────────────────────────┐
│ [▼] [📊] Project Alpha [Current] [Active]           │
│  │   │        │            │         │              │
│  │   │        │            │         └─ Status      │
│  │   │        │            └─────────── Badge       │
│  │   │        └────────────────────────── Title     │
│  │   └───────────────────────────────────── Icon    │
│  └───────────────────────────────────────── Toggle  │
└─────────────────────────────────────────────────────┘
```

### Components Breakdown:
1. **Toggle Button** (▼/▶): Expand/collapse children
2. **Type Icon** (📊): Entry type with color
3. **Title Link**: Clickable, opens entry in new tab
4. **Badge**: Shows if Current, Parent, or neither
5. **Status**: Entry status (color-coded)
6. **Relationship Label**: "Child of", "Parent of", etc.

## Empty State

When no hierarchical relationships exist:

```
┌──────────────────────────────────────────┐
│                                          │
│              🌲                          │
│                                          │
│   No hierarchical relationships found    │
│                                          │
│   Parent-child relationships will        │
│   appear here                            │
│                                          │
└──────────────────────────────────────────┘
```

## Loading State

When hierarchy is being fetched:

```
┌──────────────────────────────────────────┐
│                                          │
│              ⏳                          │
│                                          │
│        Loading hierarchy...              │
│                                          │
└──────────────────────────────────────────┘
```

## Error State

When loading fails:

```
┌──────────────────────────────────────────┐
│  ⚠️ Error Loading Hierarchy               │
│                                          │
│  Failed to fetch relationship data       │
│                                          │
│           [🔄 Retry]                     │
└──────────────────────────────────────────┘
```

## Interaction Examples

### 1. Expanding a Node
```
Before:
▶ 📊 Project Alpha

After clicking ▶:
▼ 📊 Project Alpha
  ├─ 📋 Feature 1
  └─ 📋 Feature 2
```

### 2. Collapsing a Node
```
Before:
▼ 📊 Project Alpha
  ├─ 📋 Feature 1
  └─ 📋 Feature 2

After clicking ▼:
▶ 📊 Project Alpha
```

### 3. Clicking a Title
```
Clicking "Feature 1" → Opens /entry/123/v2 in new tab
```

### 4. Hovering
```
Before hover:
  📋 Feature Development

During hover:
┌─────────────────────────────┐
│ 📋 Feature Development      │ ← Background changes
└─────────────────────────────┘
```

## Real-World Example: Project Management

```
Project Management Hierarchy:

▼ 🏢 Company Website Redesign [Parent]
  │
  ├─ ▼ 📊 Phase 1: Planning [Current]
  │  │
  │  ├─ ✅ Research competitors [Completed]
  │  ├─ ✅ User interviews [Completed]
  │  └─ ⏳ Create wireframes [In Progress]
  │
  ├─ ▶ 📊 Phase 2: Design
  │
  └─ ▶ 📊 Phase 3: Development
```

## Keyboard Shortcuts (Future Enhancement)

Could be added:
- `→` - Expand node
- `←` - Collapse node
- `↑/↓` - Navigate nodes
- `Enter` - Open entry
- `/` - Search in tree

## Mobile View

On mobile devices (< 768px):
- Reduced indentation (10px per level)
- Smaller icons
- Touch-friendly toggle buttons
- Optimized for vertical scrolling

```
Mobile Layout:
┌────────────────────┐
│ [📋] [🌲]         │ ← Tabs stack
├────────────────────┤
│ ▼ 📊 Project       │
│  ├─ 📋 Task 1      │
│  └─ 📋 Task 2      │
└────────────────────┘
```

## Performance Considerations

- **Lazy Loading**: Hierarchy only loads when tab is activated
- **Max Depth**: Limited to 3 levels by default
- **Caching**: Once loaded, data is cached until page reload
- **Smooth Animations**: CSS transitions for better UX

---

**Tip**: Use the hierarchy view to understand the structure of your relationships at a glance!
