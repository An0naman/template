#!/bin/bash
# Quick diagnostic for Entry 89 sensor data

echo "🔍 Diagnosing Sensor Data Display for Entry 89"
echo "=============================================="
echo ""

# Get the port from docker-compose (network_mode: host means it uses localhost)
PORT=5000

echo "1️⃣ Checking if container is running..."
if docker ps | grep -q template; then
    echo "   ✅ Container is running"
else
    echo "   ❌ Container is not running"
    exit 1
fi

echo ""
echo "2️⃣ Testing sensor-types endpoint..."
RESPONSE=$(curl -s "http://localhost:$PORT/api/entry/89/sensor-types")
if [ $? -eq 0 ]; then
    echo "   ✅ API responded"
    echo "   Response: $RESPONSE"
else
    echo "   ❌ API not responding"
fi

echo ""
echo "3️⃣ Testing sensor-data endpoint..."
RESPONSE=$(curl -s "http://localhost:$PORT/api/entry/89/sensor-data" | head -c 200)
if [ $? -eq 0 ]; then
    echo "   ✅ API responded"
    echo "   Response preview: $RESPONSE..."
else
    echo "   ❌ API not responding"
fi

echo ""
echo "4️⃣ Checking for JavaScript errors in recent logs..."
docker-compose logs --tail=50 template 2>&1 | grep -E "(undefined|TypeError|ReferenceError|sensor)" -i | tail -5

echo ""
echo "=============================================="
echo "📋 Next Steps:"
echo ""
echo "1. Open your browser to:"
echo "   http://localhost:$PORT/entry/89/v2"
echo ""
echo "2. Open Developer Tools (F12)"
echo "   - Check Console for 'Entry ID set to 89'"
echo "   - Look for any red errors"
echo ""
echo "3. Check Network tab:"
echo "   - Should see requests to /api/entry/89/sensor-types"
echo "   - Should see requests to /api/entry/89/sensor-data"
echo "   - All should return 200 status"
echo ""
echo "4. If still not working, check:"
echo "   - Does the sensor section card appear?"
echo "   - Are the static files loading (sensors.css, _sensors_functions.js)?"
echo "   - Is Chart.js loaded?"
