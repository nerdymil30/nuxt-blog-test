#!/usr/bin/env python3
"""
Analyze a single WordPress post in detail to understand structure
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent
XML_FILE = PROJECT_ROOT / 'AAII-Migration-assets' / 'aaiilaorg.WordPress.2025-11-01.xml'

def main():
    """Extract and analyze July 2025 Webinar post"""

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    namespaces = {
        'wp': 'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'dc': 'http://purl.org/dc/elements/1.1/',
    }

    # Find the July 2025 Webinar post (ID 17614)
    items = root.findall('.//item')
    target_post = None

    for item in items:
        post_id_elem = item.find('wp:post_id', namespaces)
        if post_id_elem is not None and post_id_elem.text == '17614':
            target_post = item
            break

    if not target_post:
        print("Could not find July 2025 Webinar post")
        return

    # Extract basic data
    title_elem = target_post.find('title')
    title = title_elem.text if title_elem is not None else ""

    content_elem = target_post.find('content:encoded', namespaces)
    content = content_elem.text if content_elem is not None else ""

    print("=" * 100)
    print(f"POST: {title}")
    print("=" * 100)
    print("\nFULL CONTENT (first 3000 characters):\n")
    print(content[:3000])
    print("\n" + "=" * 100)
    print("\nSTRUCTURE ANALYSIS:")
    print("=" * 100)

    # Find all TOPIC sections
    print("\n1. TOPIC HEADINGS:")
    topic_headings = re.findall(r'\[dfd_heading[^\]]*\]([^[]*TOPIC[^[]*)\[/dfd_heading\]', content, re.IGNORECASE)
    for i, heading in enumerate(topic_headings, 1):
        print(f"   Topic {i}: {heading[:100]}")

    # Find all SPEAKER names
    print("\n2. SPEAKER NAMES:")
    speakers = re.findall(r'team_member_name="([^"]*)"', content)
    for i, speaker in enumerate(speakers, 1):
        print(f"   Speaker {i}: {speaker}")

    # Find all SPEAKER TITLES
    print("\n3. SPEAKER TITLES:")
    speaker_titles = re.findall(r'team_member_job_position="([^"]*)"', content)
    for i, title_text in enumerate(speaker_titles, 1):
        print(f"   Title {i}: {title_text}")

    # Find button links
    print("\n4. BUTTONS/LINKS:")
    buttons = re.findall(r'button_text="([^"]*)".*?buttom_link_src="url:([^|"]*)', content, re.DOTALL)
    for i, (text, url) in enumerate(buttons, 1):
        print(f"   Button {i}: {text}")
        print(f"      URL: {url}")

    # Look at a specific topic section structure
    print("\n5. FIRST COMPLETE TOPIC SECTION:")
    print("-" * 100)
    first_topic_match = re.search(r'TOPIC\s+1[^T]+(.*?)(?=TOPIC\s+2|archiveMaterials|$)', content, re.IGNORECASE | re.DOTALL)
    if first_topic_match:
        topic_section = first_topic_match.group(1)[:1500]
        print(topic_section)
    print("-" * 100)

    # Look for topic presentation titles (the actual topic names, not just "TOPIC 1")
    print("\n6. PRESENTATION TITLES (after speaker info):")
    print("-" * 100)
    presentation_titles = re.findall(r'\[dfd_heading[^\]]*\]([^[]*?)\[/dfd_heading\](?=\[vc_column_text\])', content, re.IGNORECASE | re.DOTALL)
    for i, title_text in enumerate(presentation_titles, 1):
        print(f"   {i}. {title_text[:150]}")
    print("-" * 100)

if __name__ == '__main__':
    main()
