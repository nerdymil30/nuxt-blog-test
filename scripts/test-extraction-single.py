#!/usr/bin/env python3
"""
Test Extraction Script - Analyze single XML file
This script tests the extraction logic on a single post to identify issues
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re
import json
from urllib.parse import unquote
import html

PROJECT_ROOT = Path(__file__).parent.parent
INDIVIDUAL_POSTS_DIR = PROJECT_ROOT / 'AAII-Migration-assets' / 'individual-posts'

def get_text(element, namespaces=None):
    """Safely get text from XML element"""
    if element is None:
        return ""
    return element.text or ""

def extract_shortcode_content(content, shortcode_name):
    """Extract content between opening and closing shortcode tags"""
    pattern = rf'\[{shortcode_name}[^\]]*\](.*?)\[/{shortcode_name}\]'
    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    return matches

def extract_shortcode_params(content, shortcode_name):
    """Extract attributes from shortcode opening tag"""
    pattern = rf'\[{shortcode_name}\s+([^\]]*)\]'
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        return {}

    attrs_str = match.group(1)
    params = {}

    # Extract key="value" patterns
    attr_pattern = r'(\w+)="([^"]*)"'
    for attr_match in re.finditer(attr_pattern, attrs_str):
        key = attr_match.group(1)
        value = attr_match.group(2)
        # Try to decode URL-encoded values
        try:
            value = unquote(value)
        except:
            pass
        params[key] = value

    return params

def analyze_post(xml_file_path):
    """Analyze a single XML file"""

    print(f"\n{'='*100}")
    print(f"ANALYZING: {xml_file_path.name}")
    print(f"{'='*100}\n")

    # Parse XML
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    namespaces = {
        'wp': 'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'dc': 'http://purl.org/dc/elements/1.1/',
    }

    # Extract basic info
    title = get_text(root.find('title'))
    post_id = get_text(root.find('wp:post_id', namespaces))
    post_date = get_text(root.find('wp:post_date_gmt', namespaces))
    content = get_text(root.find('content:encoded', namespaces))
    description = get_text(root.find('description'))

    print(f"BASIC INFO:")
    print(f"  Title: {title}")
    print(f"  Post ID: {post_id}")
    print(f"  Date: {post_date}")
    print(f"  Description: {description[:100] if description else '(empty)'}")
    print(f"  Content length: {len(content)} characters\n")

    # ===== ANALYZE SHORTCODES =====
    print(f"{'='*100}")
    print("SHORTCODE ANALYSIS")
    print(f"{'='*100}\n")

    # Find all shortcodes
    all_shortcodes = re.findall(r'\[([a-z_]+)', content, re.IGNORECASE)
    unique_shortcodes = list(set(all_shortcodes))
    print(f"Shortcodes found: {', '.join(sorted(unique_shortcodes))}\n")

    # ===== ANALYZE TOPIC STRUCTURE =====
    print(f"{'='*100}")
    print("TOPIC STRUCTURE ANALYSIS")
    print(f"{'='*100}\n")

    # Find all [dfd_heading] tags
    heading_matches = re.finditer(r'\[dfd_heading[^\]]*\]([^[]*)\[/dfd_heading\]', content, re.IGNORECASE | re.DOTALL)
    headings = [m.group(1).strip() for m in heading_matches]

    print(f"Total [dfd_heading] tags: {len(headings)}")
    for i, heading in enumerate(headings[:10], 1):  # Show first 10
        print(f"  {i}. {heading[:80]}")
    if len(headings) > 10:
        print(f"  ... and {len(headings) - 10} more")

    print("\n")

    # ===== ANALYZE SPEAKER STRUCTURE =====
    print(f"{'='*100}")
    print("SPEAKER STRUCTURE ANALYSIS")
    print(f"{'='*100}\n")

    speaker_shortcodes = re.finditer(
        r'\[dfd_new_team_member\s+([^\]]*)\]',
        content,
        re.IGNORECASE | re.DOTALL
    )

    speaker_count = 0
    for match in speaker_shortcodes:
        speaker_count += 1
        params = extract_shortcode_params(content, 'dfd_new_team_member')
        print(f"Speaker {speaker_count}:")
        for key in ['team_member_name', 'team_member_job_position', 'team_member_image']:
            if key in params:
                value = params[key]
                # Unescape HTML entities
                value = html.unescape(value)
                print(f"  {key}: {value}")
        print()

    if speaker_count == 0:
        print("No speakers found in [dfd_new_team_member] shortcodes\n")

    # ===== ANALYZE BUTTON/ARCHIVE MATERIALS =====
    print(f"{'='*100}")
    print("BUTTON/ARCHIVE MATERIALS ANALYSIS")
    print(f"{'='*100}\n")

    button_matches = re.finditer(
        r'\[dfd_button\s+([^\]]*)\]',
        content,
        re.IGNORECASE
    )

    button_count = 0
    for match in button_matches:
        button_count += 1
        attrs = match.group(1)

        # Extract button_text and buttom_link_src
        text_match = re.search(r'button_text="([^"]*)"', attrs)
        link_match = re.search(r'buttom_link_src="([^"]*)"', attrs)

        button_text = text_match.group(1) if text_match else ""
        button_link = link_match.group(1) if link_match else ""

        # Unescape
        button_text = html.unescape(button_text)
        button_link = html.unescape(button_link)

        print(f"Button {button_count}:")
        print(f"  Text: {button_text}")
        print(f"  Link: {button_link}")
        print()

    if button_count == 0:
        print("No buttons found in [dfd_button] shortcodes\n")

    # ===== ANALYZE ICON LISTS (LEARNING POINTS) =====
    print(f"{'='*100}")
    print("ICON LIST ANALYSIS (LEARNING POINTS)")
    print(f"{'='*100}\n")

    icon_list_matches = re.finditer(
        r'\[dfd_icon_list\s+([^\]]*)\]',
        content,
        re.IGNORECASE
    )

    icon_list_count = 0
    for match in icon_list_matches:
        icon_list_count += 1
        attrs = match.group(1)

        # Extract list_fields parameter
        list_fields_match = re.search(r'list_fields="([^"]*)"', attrs)
        if list_fields_match:
            list_fields_encoded = list_fields_match.group(1)

            # Unescape URL encoding
            list_fields_decoded = unquote(list_fields_encoded)

            print(f"Icon List {icon_list_count}:")
            print(f"  Encoded: {list_fields_encoded[:100]}...")
            print(f"  Decoded: {list_fields_decoded[:100]}...")

            # Try to parse as JSON
            try:
                list_fields_json = json.loads(list_fields_decoded)
                print(f"  Parsed as JSON: {len(list_fields_json)} items")
                for i, item in enumerate(list_fields_json[:3], 1):
                    print(f"    Item {i}: {item}")
                if len(list_fields_json) > 3:
                    print(f"    ... and {len(list_fields_json) - 3} more")
            except json.JSONDecodeError as e:
                print(f"  ERROR parsing JSON: {e}")

            print()

    if icon_list_count == 0:
        print("No icon lists found\n")

    # ===== ANALYZE COLUMN TEXT (DESCRIPTIONS) =====
    print(f"{'='*100}")
    print("COLUMN TEXT ANALYSIS (DESCRIPTIONS)")
    print(f"{'='*100}\n")

    column_text_matches = re.finditer(
        r'\[vc_column_text[^\]]*\](.*?)\[/vc_column_text\]',
        content,
        re.IGNORECASE | re.DOTALL
    )

    column_text_count = 0
    for match in column_text_matches:
        column_text_count += 1
        text = match.group(1).strip()
        # Remove any nested shortcodes from display
        text_clean = re.sub(r'\[.*?\]', '', text)

        print(f"Column Text {column_text_count}:")
        print(f"  Content: {text_clean[:150]}...")
        print()

    if column_text_count == 0:
        print("No column text found\n")

    # ===== IDENTIFY ISSUES =====
    print(f"{'='*100}")
    print("IDENTIFIED EXTRACTION ISSUES")
    print(f"{'='*100}\n")

    issues = []

    if len(headings) > 0 and "TOPIC" in headings[0].upper():
        issues.append("❌ Topic titles showing as labels (TOPIC 1, TOPIC 2) instead of actual presentation titles")

    if not description:
        issues.append("❌ Description field is empty - need to extract from [vc_column_text]")

    if icon_list_count == 0:
        issues.append("⚠️  No learning points found - may be using different structure")

    if button_count == 0:
        issues.append("⚠️  No archive materials found - may be using different button structure")

    if speaker_count == 0:
        issues.append("❌ No speakers extracted from [dfd_new_team_member] shortcodes")

    if issues:
        for issue in issues:
            print(f"{issue}")
    else:
        print("✓ No issues identified!")

    print(f"\n{'='*100}\n")

def main():
    """Main entry point"""

    # Find the july-2025-webinar-archive-17614.xml file
    target_file = INDIVIDUAL_POSTS_DIR / 'july-2025-webinar-archive-17614.xml'

    if not target_file.exists():
        print(f"ERROR: Target file not found: {target_file}")
        print(f"\nAvailable files:")
        for xml_file in sorted(INDIVIDUAL_POSTS_DIR.glob('*.xml'))[:10]:
            print(f"  - {xml_file.name}")
        return

    analyze_post(target_file)

if __name__ == '__main__':
    main()
