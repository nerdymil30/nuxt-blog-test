#!/usr/bin/env python3
"""
Extract Individual Meeting Items to Separate XML Files
Splits the main WordPress XML export into individual item files for easier analysis
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent
XML_FILE = PROJECT_ROOT / 'AAII-Migration-assets' / 'aaiilaorg.WordPress.2025-11-01.xml'
OUTPUT_DIR = PROJECT_ROOT / 'AAII-Migration-assets' / 'individual-posts'

def sanitize_filename(text):
    """Convert text to filename-safe format"""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters, keep only alphanumeric, hyphens, spaces
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'[-\s]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text

def main():
    """Extract individual items to separate XML files"""

    if not XML_FILE.exists():
        print(f"ERROR: XML file not found: {XML_FILE}")
        return

    print(f"Parsing: {XML_FILE}")
    print(f"Output directory: {OUTPUT_DIR}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Created output directory: {OUTPUT_DIR}\n")

    # Parse XML
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    # Define namespaces
    namespaces = {
        'wp': 'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'excerpt': 'http://wordpress.org/export/1.2/excerpt/'
    }

    # Register namespaces to preserve them in output
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    # Also register other namespaces that might be in the document
    ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
    ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
    ET.register_namespace('wp', 'http://wordpress.org/export/1.2/')
    ET.register_namespace('wfw', 'http://wellformedweb.org/CommentAPI/')
    ET.register_namespace('excerpt', 'http://wordpress.org/export/1.2/excerpt/')

    # Find all items (posts)
    items = root.findall('.//item')
    print(f"Found {len(items)} total items\n")

    # Filter for meeting archive posts
    meeting_count = 0
    extracted_count = 0

    print("=" * 80)
    print("EXTRACTING MEETING ARCHIVE POSTS")
    print("=" * 80)

    for item in items:
        title_elem = item.find('title')
        title = title_elem.text if title_elem is not None else ""

        # Check if this is an archive post
        if title and 'ARCHIVE' in title.upper():
            post_type_elem = item.find('wp:post_type', namespaces)
            post_type = post_type_elem.text if post_type_elem is not None else ""

            # Only process posts, not attachments
            if post_type == 'post':
                meeting_count += 1

                # Get post ID for filename
                post_id_elem = item.find('wp:post_id', namespaces)
                post_id = post_id_elem.text if post_id_elem is not None else 'unknown'

                # Sanitize title for filename
                safe_title = sanitize_filename(title)

                # Generate filename
                filename = f"{safe_title}-{post_id}.xml"
                filepath = OUTPUT_DIR / filename

                try:
                    # Create a minimal XML document with just this item
                    # We'll create a simple wrapper
                    item_root = ET.Element('item')

                    # Copy all child elements from original item
                    for child in item:
                        item_root.append(child)

                    # Write to file
                    tree_out = ET.ElementTree(item_root)
                    tree_out.write(filepath, encoding='utf-8', xml_declaration=True)

                    extracted_count += 1
                    print(f"{extracted_count}. {filename}")

                except Exception as e:
                    print(f"ERROR extracting '{title}': {e}")

    print("\n" + "=" * 80)
    print(f"EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Total meetings found: {meeting_count}")
    print(f"Successfully extracted: {extracted_count}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"\nTo view an individual post, open:")
    print(f"  {OUTPUT_DIR}/july-2025-webinar-archive-17614.xml")

if __name__ == '__main__':
    main()
