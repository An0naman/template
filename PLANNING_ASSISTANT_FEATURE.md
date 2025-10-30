# Planning Assistant Feature - Documentation

## Overview

The Planning Assistant is an AI-powered feature that helps users create milestone plans for their entries. It analyzes entry context, researches best practices, and generates realistic timeline proposals that can be discussed, refined, and applied.

## 🎯 Key Features

### 1. **Intelligent Context Analysis**
- Analyzes current entry details, status, and description
- Reviews available status transitions
- Considers historical notes and custom field values
- Examines related entries for context
- Learns from similar completed projects
- Incorporates sensor data patterns (if available)

### 2. **AI-Powered Plan Generation**
- Uses Google Gemini to generate milestone plans
- Researches typical timeframes for project types
- Considers intended end dates as constraints
- Provides reasoning for each milestone
- Includes confidence scoring
- Returns structured JSON format

### 3. **Interactive Refinement**
- Conversational interface for plan discussion
- Users can request adjustments to dates
- Add or remove milestone steps
- Iterate until satisfied with the plan
- Clear visualization of proposed timeline

### 4. **One-Click Application**
- Apply approved plans with single button click
- Creates EntryStateMilestone records automatically
- Logs plan application as system note
- Refreshes timeline visualization
- Avoids creating duplicate milestones

## 📋 User Flow

### Accessing Planning Mode

1. Open an entry detail page (v2 layout)
2. Navigate to AI Assistant section
3. Click "Quick Actions" dropdown
4. Select "Plan Milestones" (only visible if entry has `show_end_dates` enabled)

### Using the Planning Assistant

```
Step 1: Activation
┌─────────────────────────────────────────┐
│ User clicks "Plan Milestones"           │
│ ↓                                       │
│ Bot enters Planning Mode                │
│ Shows welcome message and capabilities  │
└─────────────────────────────────────────┘

Step 2: Plan Request
┌─────────────────────────────────────────┐
│ User: "Help me plan this fermentation"  │
│ ↓                                       │
│ Bot analyzes entry context              │
│ Gathers historical data                 │
│ Generates AI plan proposal              │
└─────────────────────────────────────────┘

Step 3: Plan Review
┌─────────────────────────────────────────┐
│ Bot displays proposed plan card:        │
│ ┌─────────────────────────────────────┐ │
│ │ 📋 Fermentation Plan (21 days)     │ │
│ │ ─────────────────────────────────── │ │
│ │ → Day 7:  Secondary Ferment        │ │
│ │ → Day 14: Cold Crash               │ │
│ │ → Day 17: Bottling                 │ │
│ │ → Day 21: Completed                │ │
│ │                                     │ │
│ │ [Apply] [Discuss] [Cancel]         │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘

Step 4: Refinement (Optional)
┌─────────────────────────────────────────┐
│ User: "Move bottling to day 15"         │
│ ↓                                       │
│ Bot regenerates plan with adjustment    │
│ Shows updated proposal                  │
└─────────────────────────────────────────┘

Step 5: Application
┌─────────────────────────────────────────┐
│ User clicks "Apply Plan"                │
│ ↓                                       │
│ Creates milestone records               │
│ Updates timeline section                │
│ Confirms success                        │
└─────────────────────────────────────────┘
```

## 🏗️ Technical Architecture

### Backend Components

#### 1. Planning Service (`app/services/planning_service.py`)

**Purpose**: Core business logic for planning functionality

**Key Methods**:
- `gather_entry_context(entry_id)` - Collects all relevant data
- `generate_plan(entry_id, user_prompt)` - Uses AI to create plan
- `apply_plan(entry_id, plan)` - Creates milestone records
- `_build_planning_prompt()` - Constructs AI prompt with context
- `_parse_ai_response()` - Extracts structured data from AI

**Context Gathering Includes**:
```python
{
    'entry': {entry details},
    'available_states': [...status options...],
    'existing_milestones': [...current milestones...],
    'notes': [...recent notes...],
    'custom_fields': [...field values...],
    'related_entries': [...linked entries...],
    'sensor_summary': {...sensor stats...},
    'similar_entries': [...completed similar entries...]
}
```

#### 2. Planning API (`app/api/planning_api.py`)

**Purpose**: HTTP endpoints for planning operations

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/entries/<id>/generate_plan` | POST | Generate milestone plan |
| `/api/entries/<id>/apply_plan` | POST | Create milestones from plan |
| `/api/entries/<id>/planning_context` | GET | Get context (debugging) |

**Request/Response Examples**:

```javascript
// Generate Plan Request
POST /api/entries/123/generate_plan
{
    "prompt": "Help me plan this brew"
}

// Generate Plan Response
{
    "success": true,
    "plan": {
        "title": "Belgian Ale Fermentation Plan",
        "duration_total_days": 21,
        "reasoning": "Based on typical ale fermentation...",
        "confidence": 0.85,
        "milestones": [
            {
                "status_name": "Secondary Ferment",
                "state_id": 5,
                "target_date": "2025-11-08",
                "duration_days": 7,
                "notes": "Transfer after gravity stable"
            }
        ]
    },
    "context_summary": "Analyzing Homebrew Batch: 'Belgian Ale #3'..."
}

// Apply Plan Request
POST /api/entries/123/apply_plan
{
    "plan": {...plan object...}
}

// Apply Plan Response
{
    "success": true,
    "milestones_created": 4,
    "message": "Successfully created 4 milestone(s)"
}
```

### Frontend Components

#### 1. Planning Mode UI (`app/templates/sections/_ai_assistant_section.html`)

**New JavaScript Functions**:

| Function | Purpose |
|----------|---------|
| `enterPlanningMode()` | Activate planning mode |
| `generatePlan(prompt)` | Call API to generate plan |
| `renderPlanCard(plan)` | Display plan visually |
| `applyPlan()` | Create milestones from plan |
| `refinePlan()` | Enter refinement conversation |
| `exitPlanningMode()` | Exit planning mode |

**State Variables**:
```javascript
var planningMode = false;      // Is planning mode active?
var currentPlan = null;        // Currently displayed plan
```

**Plan Card Structure**:
```html
<div class="plan-card">
    <div class="card border-success">
        <div class="card-header bg-success">
            📋 Plan Title (21 days)
        </div>
        <div class="card-body">
            <div class="alert alert-info">
                Reasoning explanation...
            </div>
            <div class="plan-timeline">
                <!-- Milestone steps -->
            </div>
            <div class="d-flex gap-2">
                <button onclick="applyPlan()">Apply</button>
                <button onclick="refinePlan()">Discuss</button>
                <button onclick="exitPlanningMode()">Cancel</button>
            </div>
        </div>
    </div>
</div>
```

## 🧠 AI Prompting Strategy

### System Prompt Structure

```
You are an expert project planning assistant.

ENTRY INFORMATION:
- Title, Type, Status, Description
- Created date, Intended end date
- Custom field data

AVAILABLE STATUS TRANSITIONS:
- List of states in order

CUSTOM FIELD DATA:
- Recipe details, measurements, etc.

RECENT NOTES:
- Last 5 notes for context

HISTORICAL DATA:
- Similar completed entries
- Average duration patterns

USER REQUEST:
{user's specific instructions}

TASK:
Create a milestone plan with:
1. Status name (from available states)
2. Target date (YYYY-MM-DD)
3. Duration in days
4. Reasoning notes

Respond in JSON format:
{
    "title": "...",
    "duration_total_days": X,
    "reasoning": "...",
    "confidence": 0.X,
    "milestones": [...]
}
```

### Context-Aware Intelligence

The AI considers:
- **Type-specific knowledge**: Different planning for brews vs. aging vs. gardening
- **Historical patterns**: "Your last IPA took 16 days"
- **Current constraints**: Intended end date as deadline
- **Dependencies**: Primary before secondary fermentation
- **Buffer time**: Adds contingency for delays
- **Best practices**: Industry standards for the domain

## 🔒 Validation & Safety

### Input Validation
- ✅ Entry must have `show_end_dates` enabled
- ✅ Entry type must have defined states
- ✅ AI service must be available
- ✅ Milestone dates must be valid
- ✅ States must exist in available options

### Error Handling
- 🛡️ Graceful degradation if AI unavailable
- 🛡️ JSON parsing fallback
- 🛡️ Duplicate milestone detection
- 🛡️ Transaction rollback on failure
- 🛡️ User-friendly error messages

### Data Integrity
- 📌 No duplicate milestones for same state
- 📌 Dates validated as proper format
- 📌 State IDs verified against entry type
- 📌 System note created for audit trail
- 📌 Existing milestones preserved

## 📊 Testing

### Running Tests

```bash
# Run the test suite
python test_planning_assistant.py

# Expected output:
# TEST 1: Context Gathering ✓
# TEST 2: Plan Generation ✓
# TEST 3: Plan Application ✓
```

### Test Coverage

1. **Context Gathering Test**
   - Verifies all data sources are accessible
   - Checks state availability
   - Confirms historical data retrieval

2. **Plan Generation Test**
   - Tests AI integration
   - Validates JSON parsing
   - Checks milestone structure

3. **Plan Application Test**
   - Creates test milestones
   - Verifies database records
   - Confirms system note creation

### Manual Testing Checklist

- [ ] Planning mode appears only for milestone-enabled entries
- [ ] Context summary is accurate
- [ ] Generated plan has realistic dates
- [ ] Plan card renders correctly
- [ ] Refinement conversation works
- [ ] Apply creates correct milestones
- [ ] Timeline section refreshes
- [ ] System note is logged
- [ ] Duplicate milestones are prevented
- [ ] Exit planning mode works

## 🚀 Usage Examples

### Example 1: Homebrew Planning

```
User: "Help me plan this IPA batch"

Bot: "📊 Analyzing Homebrew Batch: 'West Coast IPA #3'
     Current Status: Primary Ferment
     3 notes recorded
     Found 2 similar completed entries

     I've created a proposed plan. Let me show you:"

[Plan Card Displayed]
- Day 7: Secondary Ferment (dry hop)
- Day 12: Cold Crash
- Day 15: Bottling
- Day 29: Completed

User: "Can we add a dry hop step on day 5?"

Bot: [Regenerates plan with adjustment]

User: [Clicks Apply]

Bot: "✅ Successfully created 4 milestone(s).
     The milestones are now visible in the Progress & Status section."
```

### Example 2: Aging Project Planning

```
User: "Create a 6-month aging timeline"

Bot: [Analyzes context]
     [Generates 6-month plan with quarterly checkpoints]

User: [Reviews and applies]
```

### Example 3: Garden Planning

```
User: "Plan the growth stages for this tomato plant"

Bot: [Uses domain knowledge]
     [Creates seedling → transplant → flowering → harvest timeline]
```

## 🔧 Configuration

### Prerequisites

1. **AI Service**: Google Gemini API key configured in system parameters
2. **Entry Type**: Must have `show_end_dates = 1`
3. **States**: At least 2 states defined for entry type
4. **Intended End Date**: Recommended for better planning

### System Parameters

| Parameter | Purpose |
|-----------|---------|
| `gemini_api_key` | Google AI API authentication |
| `gemini_model_name` | Model to use (default: gemini-1.5-flash) |
| `gemini_base_prompt` | Base system prompt for AI |

### Database Schema

**Uses Existing Tables**:
- `EntryStateMilestone` - Stores created milestones
- `EntryState` - Available status transitions
- `Note` - System notes for audit trail
- `Entry` - Source entry data
- `CustomFieldValue` - Additional context

**No Schema Changes Required** ✅

## 🎨 UI/UX Design Principles

1. **Discoverability**: Only shown when feature is available
2. **Clarity**: Clear visual hierarchy in plan cards
3. **Flexibility**: Easy to refine before committing
4. **Safety**: Requires explicit user action to apply
5. **Feedback**: Confirmation messages for all actions
6. **Integration**: Seamless with existing timeline section

## 📈 Future Enhancements

Potential improvements for future versions:

- [ ] Visual drag-and-drop milestone editor
- [ ] Auto-adjust milestones based on actual progress
- [ ] Email/notification reminders for upcoming milestones
- [ ] Template library for common project types
- [ ] Gantt chart visualization
- [ ] Export plans to PDF/calendar
- [ ] Multi-entry batch planning
- [ ] Progress tracking analytics
- [ ] Milestone dependencies (blockers)
- [ ] What-if scenario modeling

## 🐛 Troubleshooting

### "AI service is not available"
**Cause**: Gemini API key not configured
**Solution**: Set `gemini_api_key` in system parameters

### "Plan Milestones option not visible"
**Cause**: Entry type doesn't support milestones
**Solution**: Enable `show_end_dates` for entry type

### "No available states for planning"
**Cause**: Entry type has only one state
**Solution**: Create additional states for the entry type

### "Failed to parse AI response"
**Cause**: AI returned non-JSON or malformed JSON
**Solution**: Check logs for raw response, retry generation

### Milestones not appearing in timeline
**Cause**: Timeline section not refreshing
**Solution**: Manually refresh page or check `window.timelineModule.refresh()`

## 📝 API Integration Examples

### Using in Custom Scripts

```python
from app.services.planning_service import get_planning_service

# Generate a plan
service = get_planning_service()
result = service.generate_plan(
    entry_id=123,
    user_prompt="Create a 30-day timeline"
)

if result['success']:
    plan = result['plan']
    print(f"Generated {len(plan['milestones'])} milestones")
    
    # Apply the plan
    apply_result = service.apply_plan(123, plan)
    print(apply_result['message'])
```

### Using via HTTP API

```bash
# Generate plan
curl -X POST http://localhost:5001/api/entries/123/generate_plan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Help me plan this project"}'

# Apply plan
curl -X POST http://localhost:5001/api/entries/123/apply_plan \
  -H "Content-Type: application/json" \
  -d '{"plan": {...}}'
```

## 📚 Related Documentation

- `MILESTONE_TEMPLATES_IMPLEMENTATION.md` - Milestone template system
- `FRAMEWORK_COMPLETE.md` - Overall framework architecture
- `app/services/ai_service.py` - AI service implementation
- `migrations/add_entry_state_milestones.py` - Milestone schema

## 🎉 Summary

The Planning Assistant feature brings AI-powered intelligence to project planning:

✨ **Smart**: Learns from history and domain knowledge
✨ **Interactive**: Conversational refinement before committing
✨ **Integrated**: Seamlessly works with existing milestone system
✨ **Flexible**: Adapts to different project types
✨ **Safe**: Requires explicit user approval

**Ready to use!** Just activate Planning Mode from the AI Assistant dropdown on any milestone-enabled entry.
