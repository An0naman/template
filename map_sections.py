#!/usr/bin/env python3
"""
DEPRECATED: This script was for entry_detail.html (v1) which has been removed.
The v2 template (entry_detail_v2.html) is now the only version.
This file can be safely deleted.
"""

import re

# Read the template file
with open('app/templates/entry_detail.html', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Find all section headers with titles
sections = []
for i, line in enumerate(lines, 1):
    # Look for section titles
    if 'section-title' in line:
        print(f"Line {i}: {line.strip()[:100]}")
        # Extract the icon and title
        icon_match = re.search(r'fa-([a-z-]+)', line)
        # Look ahead to next line for title text
        if i < len(lines):
            next_line = lines[i]
            title_match = re.search(r'<i class="fas.*?</i>(.*?)(?:</h|$)', line + next_line)
            if title_match:
                title = title_match.group(1).strip()
                icon = icon_match.group(1) if icon_match else 'unknown'
                sections.append({
                    'line': i,
                    'title': title,
                    'icon': icon
                })

# Print findings
print(f"\n\nFound {len(sections)} sections:\n")
for s in sections:
    print(f"Line {s['line']}: {s['title']} (icon: fa-{s['icon']})")
