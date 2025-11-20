# Draw.io AI Analysis - Quick Start Guide

## 🚀 How to Use

### Step 1: Create Your Diagram
Navigate to any entry with a Draw.io section and create your diagram using the embedded editor.

```
┌─────────────────────────────────────┐
│  Diagram Editor                 ⚙️  │
│  ┌─────┐  Save  Clear  Export  🤖  │
│  │     │                            │
│  │  📊 │  ← Your Diagram Here      │
│  │     │                            │
│  └─────┘                            │
└─────────────────────────────────────┘
```

### Step 2: Click "Send to AI"
Look for the new **🤖 Send to AI** button in the top-right corner of the diagram editor.

**Button Location:**
```
[Save] [Clear] [Export] [🤖 Send to AI]
                         ↑
                    Click here!
```

### Step 3: View Analysis
The AI Assistant section will automatically scroll into view with your analysis.

```
┌─────────────────────────────────────┐
│  AI Assistant                       │
├─────────────────────────────────────┤
│  You: Analyze my current diagram    │
│                                      │
│  🤖 AI Assistant:                   │
│  📊 Diagram Statistics:             │
│  - Total elements: 12                │
│  - Shapes/Nodes: 7                   │
│  - Connections: 5                    │
│  - Has labels: Yes                   │
│                                      │
│  What the diagram represents:        │
│  This appears to be...               │
│                                      │
│  Key components:                     │
│  1. API Gateway                      │
│  2. User Service                     │
│  ...                                 │
│                                      │
│  Observations:                       │
│  - Good separation of concerns       │
│  - Consider adding...                │
│                                      │
│  Questions:                          │
│  - What protocol are...              │
└─────────────────────────────────────┘
```

## 💡 What You Get

### 1. Diagram Statistics
Instant overview of your diagram:
- **Total elements**: All components
- **Vertices**: Shapes and boxes
- **Edges**: Connections between elements
- **Labels**: Text content present

### 2. Purpose Analysis
AI identifies:
- What type of diagram it is
- Main purpose and goal
- Domain/context

### 3. Component Breakdown
Detailed list of:
- Key elements
- Their relationships
- How they interact

### 4. Observations & Suggestions
- Pattern recognition
- Best practice recommendations
- Potential issues
- Improvement ideas

### 5. Clarifying Questions
AI asks about:
- Missing details
- Ambiguous connections
- Design decisions

## 🎯 Use Cases

### System Architecture Review
```
You: [Create architecture diagram]
     [Send to AI]

AI: "This is a microservices architecture with 5 services.
     Observations:
     - Missing API gateway
     - No load balancer shown
     - Consider adding message queue"
```

### Flowchart Validation
```
You: [Create login flowchart]
     [Send to AI]

AI: "User authentication flow detected.
     Observations:
     - Missing 2FA step
     - No 'forgot password' path
     - Consider rate limiting"
```

### Wiring Diagram Check
```
You: [Create ESP32 wiring diagram]
     [Send to AI]

AI: "Hardware connection diagram for ESP32.
     Components detected:
     - DHT22 sensor on GPIO 4
     - LED on GPIO 2
     - Push button on GPIO 5
     
     Suggestions:
     - Add pull-down resistor to button
     - Consider VCC/GND connections"
```

### Database Schema Review
```
You: [Create ER diagram]
     [Send to AI]

AI: "Entity-Relationship diagram with 4 tables.
     Observations:
     - One-to-many relationships correct
     - Missing indexes on foreign keys
     - Consider adding User table"
```

## 🔄 Follow-Up Interaction

After analysis, continue the conversation:

```
AI: [Provides initial analysis]

You: "What if I add a caching layer?"

AI: "Adding a cache layer would improve performance by:
     - Reducing database load
     - Faster response times
     - Better scalability
     
     I recommend placing it between the API and database.
     Would you like me to suggest specific technologies?"

You: "Yes, suggest some options"

AI: "For your use case, consider:
     1. Redis - Fast, in-memory
     2. Memcached - Simple, distributed
     3. Elasticsearch - If you need search..."
```

## ⚡ Pro Tips

### 1. Add Meaningful Labels
```
Good: "User Service", "Payment API", "Database"
Better: Detailed labels help AI understand context
```

### 2. Keep Diagrams Organized
```
✅ Clear structure
✅ Logical grouping
✅ Consistent naming
❌ Overlapping elements
❌ Unclear connections
```

### 3. Use for Iterations
```
1. Create initial diagram
2. Send to AI for feedback
3. Make improvements
4. Send updated version
5. Compare insights
```

### 4. Ask Specific Questions
After analysis:
```
"How can I improve security?"
"What if traffic increases 10x?"
"Is this following REST principles?"
"Suggest monitoring points"
```

### 5. Context Matters
AI considers:
- Entry title
- Entry description
- Entry type
- Your questions in chat

## 🎨 Example Diagrams to Try

### Simple 3-Node System
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Client  │───▶│  API    │───▶│Database │
└─────────┘    └─────────┘    └─────────┘
```

### Branching Flow
```
        ┌────────┐
        │ Start  │
        └───┬────┘
            │
        ┌───▼────┐
        │Process │
        └───┬────┘
            │
      ┌─────┴─────┐
      │           │
  ┌───▼───┐   ┌───▼───┐
  │Success│   │Failure│
  └───────┘   └───────┘
```

### Hub and Spoke
```
     ┌────┐
     │ S1 │
     └─┬──┘
  ┌────▼────┐
  │  Hub    │
  └─┬───┬───┘
    │   └──────┐
┌───▼─┐     ┌──▼──┐
│ S2  │     │ S3  │
└─────┘     └─────┘
```

## ⚙️ Behind the Scenes

### What Happens:
1. **Capture**: Diagram XML extracted from Draw.io
2. **Parse**: XML analyzed for structure and content
3. **Context**: Entry information gathered
4. **Analyze**: AI processes diagram with context
5. **Present**: Results shown in chat with statistics

### Data Sent:
- Diagram XML structure
- Entry ID (for context)
- Entry title, description, type
- No sensitive data unless in your diagram

### Privacy:
- Data sent only to configured AI service (Gemini)
- Not stored permanently
- Follows existing entry permissions

## 🚨 Troubleshooting

### Button Not Working?
1. Check Draw.io editor is loaded (iframe appears)
2. Refresh the page
3. Check browser console for errors

### No Analysis Appears?
1. Verify AI Assistant section exists on page
2. Check Gemini API key is configured
3. Ensure diagram has content (not blank)

### Partial or Generic Analysis?
1. Add more labels to your diagram
2. Include descriptive text
3. Provide context in entry description
4. Ask follow-up questions for details

### "AI service not available" Error?
1. Go to Settings → AI Configuration
2. Enter valid Gemini API key
3. Save and retry

## 📋 Keyboard Shortcuts

While in Draw.io editor:
- `Ctrl+S` / `Cmd+S` - Save diagram
- `Ctrl+Z` / `Cmd+Z` - Undo
- `Ctrl+Y` / `Cmd+Y` - Redo
- `Delete` - Remove selected element

Then click **🤖 Send to AI** for instant analysis!

## 🎓 Learn More

### Related Features:
- **AI Description Generator** - Generate entry descriptions
- **Planning Assistant** - Create milestone plans
- **Compose Note** - AI-assisted note writing
- **Diagram Generator** - Create diagrams from text (reverse flow)

### Best Practices:
1. **Start Simple**: Test with basic diagrams first
2. **Iterate**: Use feedback to improve
3. **Document**: Keep analyses for reference
4. **Collaborate**: Share insights with team
5. **Version Control**: Save diagram versions as you iterate

---

## 🎉 Ready to Start!

1. Open any entry
2. Find the Draw.io section
3. Create your diagram
4. Click **🤖 Send to AI**
5. Get instant insights!

**Questions?** Ask the AI Assistant - it's there to help! 🚀
