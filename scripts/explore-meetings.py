#!/usr/bin/env python3
"""
WordPress Meetings Explorer
Lists all meeting archive posts to analyze extraction issues
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
XML_FILE = PROJECT_ROOT / 'AAII-Migration-assets' / 'aaiilaorg.WordPress.2025-11-01.xml'

def get_text(element, namespaces=None):
    """Safely get text from XML element"""
    if element is None:
        return ""
    return element.text or ""

def count_topics(html_content):
    """Count TOPIC sections in HTML content"""
    return len(re.findall(r'\[dfd_heading[^\]]*\].*?TOPIC\s+\d+', html_content, re.IGNORECASE | re.DOTALL))

def extract_first_topic_title(html_content):
    """Extract the title of the first topic"""
    match = re.search(r'TOPIC\s+1[^\[]*\[dfd_heading[^\]]*\]([^[]*)\[/dfd_heading\]', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()[:100]
    return "Unknown"

def main():
    """Parse XML and list all meeting posts"""

    if not XML_FILE.exists():
        print(f"ERROR: XML file not found: {XML_FILE}")
        return

    print(f"Parsing: {XML_FILE}\n")
    print("=" * 100)

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    # Define namespaces
    namespaces = {
        'wp': 'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'excerpt': 'http://wordpress.org/export/1.2/excerpt/'
    }

    # Find all items (posts)
    items = root.findall('.//item')

    # Filter for meeting archive posts
    meetings = []
    for item in items:
        title_elem = item.find('title')
        title = title_elem.text if title_elem is not None else ""

        if title and 'ARCHIVE' in title.upper():
            post_type_elem = item.find('wp:post_type', namespaces)
            post_type = post_type_elem.text if post_type_elem is not None else ""

            if post_type == 'post':
                # Extract data
                post_id_elem = item.find('wp:post_id', namespaces)
                post_id = post_id_elem.text if post_id_elem is not None else ""

                post_date_elem = item.find('wp:post_date_gmt', namespaces)
                post_date = post_date_elem.text if post_date_elem is not None else ""

                content_elem = item.find('content:encoded', namespaces)
                content = content_elem.text if content_elem is not None else ""

                description_elem = item.find('description')
                description = description_elem.text if description_elem is not None else ""

                # Count topics
                num_topics = count_topics(content)
                first_topic = extract_first_topic_title(content)

                meetings.append({
                    'id': post_id,
                    'title': title,
                    'date': post_date,
                    'description': description[:50] if description else "(no description)",
                    'num_topics': num_topics,
                    'first_topic': first_topic,
                    'content_length': len(content)
                })

    # Display results
    print(f"\nFOUND {len(meetings)} MEETING ARCHIVE POSTS\n")
    print("=" * 100)

    for i, meeting in enumerate(meetings, 1):
        print(f"\n{i}. POST ID: {meeting['id']}")
        print(f"   Title: {meeting['title']}")
        print(f"   Date: {meeting['date']}")
        print(f"   Description: {meeting['description']}")
        print(f"   Topics found: {meeting['num_topics']}")
        if meeting['num_topics'] > 0:
            print(f"   First topic: {meeting['first_topic']}")
        print(f"   Content size: {meeting['content_length']} bytes")
        print("-" * 100)

    # Summary statistics
    print("\n" + "=" * 100)
    print("\nSUMMARY STATISTICS:")
    print(f"Total meetings: {len(meetings)}")
    print(f"Posts with topics: {sum(1 for m in meetings if m['num_topics'] > 0)}")
    print(f"Posts without topics: {sum(1 for m in meetings if m['num_topics'] == 0)}")
    print(f"Average topics per post: {sum(m['num_topics'] for m in meetings) / len(meetings):.1f}")
    print(f"Total topics: {sum(m['num_topics'] for m in meetings)}")

    # Show posts without topics
    no_topic_posts = [m for m in meetings if m['num_topics'] == 0]
    if no_topic_posts:
        print(f"\nPosts WITHOUT topics ({len(no_topic_posts)}):")
        for m in no_topic_posts[:5]:  # Show first 5
            print(f"  - {m['title']}")

if __name__ == '__main__':
    main()
