#!/bin/bash

# Simple test script to verify theme API functionality

echo "Testing Theme API..."

# Test GET current theme settings
echo "1. Getting current theme settings:"
curl -X GET http://localhost:5000/api/theme_settings
echo -e "\n"

# Test POST new theme settings  
echo "2. Setting dark mode and purple theme:"
curl -X POST http://localhost:5000/api/theme_settings \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "purple",
    "dark_mode": true,
    "font_size": "large",
    "high_contrast": false
  }'
echo -e "\n"

# Test GET updated settings
echo "3. Getting updated theme settings:"
curl -X GET http://localhost:5000/api/theme_settings
echo -e "\n"

# Test invalid theme
echo "4. Testing invalid theme (should return error):"
curl -X POST http://localhost:5000/api/theme_settings \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "invalid_theme",
    "dark_mode": false,
    "font_size": "normal",
    "high_contrast": false
  }'
echo -e "\n"

echo "Theme API testing complete!"
