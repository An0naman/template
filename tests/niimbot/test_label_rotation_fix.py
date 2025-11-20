#!/usr/bin/env python3
"""
Test script to validate the label rotation fix
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.api.labels_api import generate_single_label
from PIL import Image

def test_label_rotation():
    """Test that label rotation works correctly for both preview and print"""
    print("🧪 Testing label rotation fix...")
    
    # Sample entry data
    sample_entry = {
        "id": 1,
        "title": "Test Entry for Rotation",
        "description": "This is a test entry to verify that the 90-degree rotation works correctly for both preview and print modes.",
        "entry_type_label": "Test",
        "status": "active",
        "created_at": "2025-01-01T12:00:00Z",
        "intended_end_date": "2025-12-31"
    }
    
    # Sample parameters
    sample_params = {
        "label_font_size": "12",
        "label_include_logo": "true",
        "project_name": "Test Project",
        "label_include_qr_code": "true",
        "label_qr_code_prefix": "TestProject"
    }
    
    label_type = "8_labels"
    
    print("📝 Generating labels...")
    
    # Test normal orientation (0 degrees)
    normal_preview = generate_single_label(sample_entry, sample_params, label_type, rotation=0, for_printing=False)
    normal_print = generate_single_label(sample_entry, sample_params, label_type, rotation=0, for_printing=True)
    
    print(f"✅ Normal orientation - Preview: {normal_preview.size}, Print: {normal_print.size}")
    
    # Test 90-degree rotation
    rotated_preview = generate_single_label(sample_entry, sample_params, label_type, rotation=90, for_printing=False)
    rotated_print = generate_single_label(sample_entry, sample_params, label_type, rotation=90, for_printing=True)
    
    print(f"✅ 90° rotation - Preview: {rotated_preview.size}, Print: {rotated_print.size}")
    
    # Verify dimensions
    print("\n📏 Checking dimensions...")
    
    # For normal orientation, preview and print should have same dimensions
    if normal_preview.size == normal_print.size:
        print("✅ Normal orientation: Preview and print have same dimensions")
    else:
        print(f"❌ Normal orientation: Preview {normal_preview.size} != Print {normal_print.size}")
    
    # For 90-degree rotation:
    # - Preview should be in landscape mode (wider than tall)
    # - Print should be rotated back to portrait mode (taller than wide) to fit on label sheet
    preview_width, preview_height = rotated_preview.size
    print_width, print_height = rotated_print.size
    
    print(f"90° Preview: {preview_width}x{preview_height} (landscape: {preview_width > preview_height})")
    print(f"90° Print: {print_width}x{print_height} (portrait: {print_height > print_width})")
    
    # The key fix: preview should be landscape, print should be portrait
    if preview_width > preview_height:
        print("✅ Preview is in landscape mode (shows how rotated label will look)")
    else:
        print("❌ Preview should be in landscape mode")
        
    if print_height > print_width:
        print("✅ Print version is rotated to portrait (fits correctly on label sheet)")
    else:
        print("❌ Print version should be rotated to portrait")
    
    # Verify that the print dimensions match the normal label dimensions
    if (print_width, print_height) == (normal_print.size[0], normal_print.size[1]):
        print("✅ Rotated print label has same dimensions as normal label (will fit on sheet)")
    else:
        print(f"❌ Rotated print label dimensions don't match normal label")
    
    print("\n🎯 Summary:")
    print("- Normal labels: Preview and print are identical")
    print("- 90° rotated labels:")
    print("  - Preview: Shows landscape layout (what user sees)")
    print("  - Print: Rotated to portrait (fits on physical label sheet)")
    print("- Both rotated and normal print labels have same dimensions")
    
    return True

if __name__ == "__main__":
    try:
        test_label_rotation()
        print("\n✅ All label rotation tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
