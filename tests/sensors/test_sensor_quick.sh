#!/bin/bash
# Quick test script for Sensor Module

echo "=========================================="
echo "🧪 Sensor Module Testing Guide"
echo "=========================================="
echo ""

# Step 1: Static validation
echo "Step 1: Running static validation..."
python3 validate_sensor_module.py
VALIDATION_RESULT=$?

if [ $VALIDATION_RESULT -eq 0 ]; then
    echo ""
    echo "✅ Static validation passed!"
    echo ""
    
    # Step 2: Check if server is running
    echo "Step 2: Checking if server is running..."
    if lsof -ti:5000 > /dev/null 2>&1; then
        echo "✅ Server is already running on port 5000"
        echo ""
        echo "You can now:"
        echo "  1. Run E2E tests: ./test_sensor_module_e2e.py"
        echo "  2. Open browser: http://localhost:5000/entry/1/v2"
    else
        echo "⚠️  Server is not running"
        echo ""
        echo "To start testing:"
        echo "  1. Start server: python3 run.py"
        echo "  2. Then run: ./test_sensor_module_e2e.py"
        echo ""
        echo "Or start server now? (y/n)"
        read -r START_SERVER
        
        if [ "$START_SERVER" = "y" ] || [ "$START_SERVER" = "Y" ]; then
            echo "Starting Flask server..."
            python3 run.py &
            SERVER_PID=$!
            echo "Server started (PID: $SERVER_PID)"
            echo "Waiting 5 seconds for server to initialize..."
            sleep 5
            
            echo ""
            echo "Running E2E tests..."
            python3 test_sensor_module_e2e.py
            TEST_RESULT=$?
            
            echo ""
            if [ $TEST_RESULT -eq 0 ]; then
                echo "✅ All E2E tests passed!"
            else
                echo "❌ Some E2E tests failed. Check output above."
            fi
            
            echo ""
            echo "Server is still running. To stop: kill $SERVER_PID"
            echo "Or visit: http://localhost:5000/entry/1/v2"
        fi
    fi
else
    echo ""
    echo "❌ Static validation failed. Please review output above."
    exit 1
fi
