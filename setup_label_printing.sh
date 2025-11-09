#!/bin/bash
# Label Printing Section Setup
# Installs required dependencies for the label printing feature

echo "=================================="
echo "Label Printing Section Setup"
echo "=================================="
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed"
    echo "Please install Python 3 and pip first"
    exit 1
fi

echo "📦 Installing Python dependencies..."
echo ""

# Install required packages
pip3 install qrcode[pil] pillow

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Dependencies installed successfully!"
else
    echo ""
    echo "❌ Error installing dependencies"
    exit 1
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Ensure your Niimbot printer is paired via Bluetooth"
echo "2. Find the printer's MAC address (XX:XX:XX:XX:XX:XX)"
echo "3. Enable the 'Label Printing' section in your entry type layout"
echo "4. Navigate to an entry and test the printer connection"
echo ""
echo "For more information, see LABEL_PRINTING_SECTION.md"
echo ""
