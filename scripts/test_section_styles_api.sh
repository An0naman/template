#!/bin/bash

# Test script for section styling functionality
echo "Testing Section Styling API..."
echo "================================="

BASE_URL="http://localhost:5000"

echo "1. Testing GET theme settings (checking for section styles)..."
curl -s -X GET "${BASE_URL}/api/theme_settings" | python3 -m json.tool

echo -e "\n\n2. Testing POST theme settings with section styles..."
curl -s -X POST "${BASE_URL}/api/theme_settings" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "purple",
    "dark_mode": false,
    "font_size": "normal",
    "high_contrast": false,
    "section_styles": {
      "border_style": "bold",
      "spacing": "spacious",
      "background": "elevated"
    }
  }' | python3 -m json.tool

echo -e "\n\n3. Testing POST theme settings with glassmorphic background..."
curl -s -X POST "${BASE_URL}/api/theme_settings" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "emerald",
    "dark_mode": true,
    "font_size": "large",
    "high_contrast": false,
    "section_styles": {
      "border_style": "rounded",
      "spacing": "normal",
      "background": "glassmorphic"
    }
  }' | python3 -m json.tool

echo -e "\n\n4. Testing POST theme settings with sharp borders and compact spacing..."
curl -s -X POST "${BASE_URL}/api/theme_settings" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "amber",
    "dark_mode": false,
    "font_size": "small",
    "high_contrast": false,
    "section_styles": {
      "border_style": "sharp",
      "spacing": "compact",
      "background": "flat"
    }
  }' | python3 -m json.tool

echo -e "\n\n5. Testing invalid section style values..."
curl -s -X POST "${BASE_URL}/api/theme_settings" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "default",
    "section_styles": {
      "border_style": "invalid",
      "spacing": "invalid",
      "background": "invalid"
    }
  }' | python3 -m json.tool

echo -e "\n\n6. Final GET to verify current settings..."
curl -s -X GET "${BASE_URL}/api/theme_settings" | python3 -m json.tool

echo -e "\n\nSection styling API test completed!"
echo "Check the responses above for proper section_styles handling."
