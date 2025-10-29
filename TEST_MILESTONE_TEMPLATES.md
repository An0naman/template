# Testing Milestone Templates in Docker

## Current Build Status
Building new Docker image with milestone templates feature: `ghcr.io/an0naman/template:milestone-test`

## Quick Test Process

### Option 1: Update Existing Container (Recommended)

1. **Stop one of your running containers:**
   ```bash
   docker stop projects  # or devops
   ```

2. **Update the docker-compose.yml to use the new image:**
   ```yaml
   image: ghcr.io/an0naman/template:milestone-test
   ```

3. **Restart the container:**
   ```bash
   docker-compose up -d projects
   ```

4. **Run the test script:**
   ```bash
   python test_milestone_templates.py
   ```

### Option 2: Test Locally (Quick Dev Test)

1. **Start the app directly:**
   ```bash
   python run.py
   ```

2. **Update test script to use localhost:5000:**
   ```python
   BASE_URL = "http://localhost:5000"
   ```

3. **Run tests:**
   ```bash
   python test_milestone_templates.py
   ```

### Option 3: Create Temporary Test Container

```bash
# Create a test directory
mkdir -p /tmp/milestone-test/data

# Run temporary container
docker run -d \
  --name milestone-test \
  -p 5999:5001 \
  -v /tmp/milestone-test/data:/app/data \
  ghcr.io/an0naman/template:milestone-test

# Update test script
# BASE_URL = "http://localhost:5999"

# Run tests
python test_milestone_templates.py

# Clean up when done
docker stop milestone-test
docker rm milestone-test
```

## What the Test Script Validates

### Part 1: Entry Type Relationships
- ✅ Gets all entry types
- ✅ Creates relationship between two entry types
- ✅ Verifies relationship was created

### Part 2: Milestone Templates
- ✅ Marks entry as template with name/description
- ✅ Verifies template configuration
- ✅ Toggles distribution status
- ✅ Browses available templates
- ✅ Imports template into target entry
- ✅ Verifies milestones were imported
- ✅ Checks date recalculation

## Manual Browser Testing

Once the container is running, you can also test via browser:

1. **Go to:** http://localhost:5003 (or your port)

2. **Create a Template:**
   - Open an entry that has milestones
   - In "Progress & Status" section, find the Template dropdown
   - Click "Save as Template"
   - Fill in name/description
   - Check "Mark for distribution"
   - Save

3. **Import a Template:**
   - Open another entry of the same type
   - Click Template → "Import from Template"
   - Browse available templates
   - Select one and choose import mode
   - Import

4. **Verify:**
   - Check that milestones appear
   - Verify dates are recalculated
   - Confirm progress bars update

## Troubleshooting

### Test fails with 404 errors
- Container is using old image without new API endpoints
- Rebuild and restart container with new image

### No milestones in source entry
```bash
# Add test milestones first via API or UI
curl -X POST http://localhost:5003/api/entries/1/milestones \
  -H "Content-Type: application/json" \
  -d '{
    "milestone_order": 1,
    "milestone_title": "Planning",
    "milestone_state": "completed",
    "milestone_days": 7
  }'
```

### No entry types available
- Database might be empty
- Create some entry types first via the UI

## Current Running Instances

Your active Docker containers:
- **projects**: Port 5003
- **devops**: Port 5002

Both are running the old image and need to be updated to test the new feature.
