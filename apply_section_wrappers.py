#!/usr/bin/env python3
"""
DEPRECATED: This script was for entry_detail.html (v1) which has been removed.
The v2 template (entry_detail_v2.html) is now the only version.
This file can be safely deleted.
"""

# Define all sections that need the pattern applied
# Format: (section_name, start_marker, end_marker)
SECTIONS = [
    # Relationships section (if exists)
    ('relationships', '<!-- Relationships Section -->', '<!-- End Relationships Section -->'),
    # Labels section (actually label_printing)
    ('label_printing', '<!-- Label Printing Section', '<!-- End Label Printing'),
    # Sensors section
    ('sensors', '<!-- Sensors Section', '<!-- End Sensors'),
    # Reminders section  
    ('reminders', '<!-- Reminders Section', '<!-- End Reminders'),
    # Attachments section
    ('attachments', '<!-- Attachments Section', '<!-- End Attachments'),
    # Form Fields section
    ('form_fields', '<!-- Form Fields Section', '<!-- End Form Fields'),
    # QR Code section
    ('qr_code', '<!-- QR Code Section', '<!-- End QR Code'),
    # Timeline section
    ('timeline', '<!-- Timeline Section', '<!-- End Timeline'),
    # Relationship Opportunities
    ('relationship_opportunities', '<!-- Relationship Opportunities', '<!-- End Relationship Opportunities'),
]

def generate_section_wrapper_start(section_name):
    """Generate the opening wrapper code for a section"""
    return f"""                {{% set {section_name}_visible = section_config.get('{section_name}', {{}}).get('visible', True) %}}
                {{% set {section_name}_width = section_config.get('{section_name}', {{}}).get('width', 12) %}}
                {{% set {section_name}_height = section_config.get('{section_name}', {{}}).get('height', 3) %}}
                {{% set {section_name}_title = section_config.get('{section_name}', {{}}).get('title', '') %}}
                {{% set {section_name}_collapsible = section_config.get('{section_name}', {{}}).get('collapsible', False) %}}
                {{% set {section_name}_collapsed = section_config.get('{section_name}', {{}}).get('collapsed', False) %}}
                
                {{% if {section_name}_visible %}}
                <div class="row">
                    <div class="col-12 col-md-{{{{ {section_name}_width }}}}">
                        {{% if {section_name}_collapsible %}}
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            {{% if {section_name}_title %}}
                            <h5 class="mb-0">{{{{ {section_name}_title }}}}</h5>
                            {{% endif %}}
                        </div>
                        <div class="collapse {{{{ 'show' if not {section_name}_collapsed else '' }}}}" id="{section_name}SectionContent">
                        {{% endif %}}
                        
"""

def generate_section_wrapper_end(section_name):
    """Generate the closing wrapper code for a section"""
    return f"""
                        {{% if {section_name}_collapsible %}}
                        </div>
                        {{% endif %}}
                    </div>
                </div>
                {{% endif %}}
"""

print("Section wrapper templates generated!")
print("\n=== START WRAPPER ===")
print(generate_section_wrapper_start('sensors'))
print("\n=== END WRAPPER ===")
print(generate_section_wrapper_end('sensors'))
