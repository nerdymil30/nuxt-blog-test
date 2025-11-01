#!/usr/bin/env python3
"""
Improved Extraction Test - Extract meeting data correctly
Demonstrates proper parsing of topics, speakers, and materials
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

def extract_topics_correct(content):
    """Extract topics with correct pairing of labels and titles"""
    topics = []

    # Find all [dfd_heading] tags with content
    heading_matches = list(re.finditer(
        r'\[dfd_heading[^\]]*\]([^[]*)\[/dfd_heading\]',
        content,
        re.IGNORECASE | re.DOTALL
    ))

    headings = [(m.group(1).strip(), m.start()) for m in heading_matches]

    print(f"DEBUG: Found {len(headings)} headings")
    for i, (text, pos) in enumerate(headings):
        print(f"  {i}: {text[:60]}")

    # Find TOPIC N labels and pair with following heading
    topic_num = 1
    for i, (heading_text, heading_pos) in enumerate(headings):
        if f"TOPIC {topic_num}" in heading_text.upper():
            # Next heading should be the actual title
            if i + 1 < len(headings):
                actual_title = headings[i + 1][0]
                # Make sure it's not another TOPIC label
                if "TOPIC" not in actual_title.upper():
                    topics.append({
                        'number': topic_num,
                        'label': heading_text,
                        'title': actual_title
                    })
                    topic_num += 1

    return topics

def extract_speakers_correct(content):
    """Extract speakers with proper parsing of [dfd_new_team_member] shortcodes"""
    speakers = []

    # Find all [dfd_new_team_member ...] shortcodes
    speaker_matches = re.finditer(
        r'\[dfd_new_team_member\s+([^\]]*)\]',
        content,
        re.IGNORECASE | re.DOTALL
    )

    seen_speakers = set()  # Track to avoid duplicates

    for match in speaker_matches:
        attrs_str = match.group(1)

        # Extract key="value" attributes
        params = {}
        for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
            key = attr_match.group(1)
            value = attr_match.group(2)
            # Unescape URL encoding if needed
            try:
                value = unquote(value)
            except:
                pass
            # Unescape HTML entities
            value = html.unescape(value)
            params[key] = value

        name = params.get('team_member_name', '').strip()
        title = params.get('team_member_job_position', '').strip()

        # Skip duplicates
        speaker_key = (name, title)
        if speaker_key not in seen_speakers:
            speakers.append({
                'name': name,
                'title': title,
                'image': params.get('team_member_image', '')
            })
            seen_speakers.add(speaker_key)

    return speakers

def extract_archive_materials_correct(content):
    """Extract archive materials with proper URL decoding"""
    materials = []

    # Find all [dfd_button ...] shortcodes
    button_matches = re.finditer(
        r'\[dfd_button\s+([^\]]*)\]',
        content,
        re.IGNORECASE
    )

    for match in button_matches:
        attrs = match.group(1)

        # Extract button_text
        text_match = re.search(r'button_text="([^"]*)"', attrs)
        button_text = text_match.group(1) if text_match else ""
        button_text = html.unescape(button_text)

        # Extract buttom_link_src and clean it
        link_match = re.search(r'buttom_link_src="([^"]*)"', attrs)
        if link_match:
            button_link = link_match.group(1)

            # Extract URL from "url:..." format and remove trailing ||...
            url_match = re.search(r'url:([^|]*)', button_link)
            if url_match:
                url = url_match.group(1).strip()
                # URL decode
                url = unquote(url)
                # Unescape HTML entities
                url = html.unescape(url)

                materials.append({
                    'type': button_text,
                    'url': url
                })

    return materials

def extract_learning_points_correct(content):
    """Extract learning points from [dfd_icon_list] shortcodes"""
    all_points = []

    # Find all [dfd_icon_list ...] shortcodes
    icon_list_matches = re.finditer(
        r'\[dfd_icon_list\s+([^\]]*)\]',
        content,
        re.IGNORECASE
    )

    for match in icon_list_matches:
        attrs = match.group(1)

        # Extract list_fields parameter
        list_fields_match = re.search(r'list_fields="([^"]*)"', attrs)
        if list_fields_match:
            list_fields_encoded = list_fields_match.group(1)

            # URL decode
            list_fields_decoded = unquote(list_fields_encoded)

            # Parse JSON
            try:
                items = json.loads(list_fields_decoded)
                for item in items:
                    if 'text_content' in item:
                        text = item['text_content'].strip()
                        # Clean up newlines
                        text = re.sub(r'\s+', ' ', text)
                        all_points.append(text)
            except json.JSONDecodeError:
                pass

    return all_points

def extract_speaker_descriptions(content):
    """Extract speaker descriptions from [vc_column_text] blocks"""
    descriptions = []

    # Find all [vc_column_text] blocks
    column_matches = re.finditer(
        r'\[vc_column_text[^\]]*\](.*?)\[/vc_column_text\]',
        content,
        re.IGNORECASE | re.DOTALL
    )

    for match in column_matches:
        text = match.group(1).strip()

        # Remove nested shortcodes
        text_clean = re.sub(r'\[.*?\]', '', text)

        # Remove HTML tags for description extraction
        # Keep if it looks like a description (has length, not a header)
        text_no_tags = re.sub(r'<[^>]*>', '', text_clean)
        text_no_tags = html.unescape(text_no_tags).strip()

        if len(text_no_tags) > 50 and not re.match(r'^(PROGRAM|ARCHIVE|Attend)', text_no_tags):
            descriptions.append(text_no_tags)

    return descriptions

def extract_post_correctly(xml_file_path):
    """Extract all data from a single post correctly"""

    print(f"\n{'='*100}")
    print(f"IMPROVED EXTRACTION: {xml_file_path.name}")
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

    print(f"BASIC INFO:")
    print(f"  Title: {title}")
    print(f"  Post ID: {post_id}")
    print(f"  Date: {post_date}\n")

    # ===== EXTRACT TOPICS =====
    print(f"{'='*100}")
    print("EXTRACTED TOPICS")
    print(f"{'='*100}\n")

    topics = extract_topics_correct(content)
    print(f"Total topics: {len(topics)}\n")
    for topic in topics:
        print(f"Topic {topic['number']}: {topic['title']}")
    print()

    # ===== EXTRACT SPEAKERS =====
    print(f"{'='*100}")
    print("EXTRACTED SPEAKERS (Deduplicated)")
    print(f"{'='*100}\n")

    speakers = extract_speakers_correct(content)
    print(f"Total speakers: {len(speakers)}\n")
    for speaker in speakers:
        print(f"• {speaker['name']}")
        print(f"  Title: {speaker['title']}")
        print(f"  Image: {speaker['image']}")
        print()

    # ===== EXTRACT ARCHIVE MATERIALS =====
    print(f"{'='*100}")
    print("EXTRACTED ARCHIVE MATERIALS (Cleaned URLs)")
    print(f"{'='*100}\n")

    materials = extract_archive_materials_correct(content)
    print(f"Total materials: {len(materials)}\n")
    for material in materials:
        print(f"• {material['type']}")
        print(f"  URL: {material['url']}")
        print()

    # ===== EXTRACT LEARNING POINTS =====
    print(f"{'='*100}")
    print("EXTRACTED LEARNING POINTS")
    print(f"{'='*100}\n")

    learning_points = extract_learning_points_correct(content)
    print(f"Total learning points: {len(learning_points)}\n")
    for i, point in enumerate(learning_points, 1):
        print(f"{i}. {point}")
    print()

    # ===== EXTRACT DESCRIPTIONS =====
    print(f"{'='*100}")
    print("EXTRACTED SPEAKER DESCRIPTIONS")
    print(f"{'='*100}\n")

    descriptions = extract_speaker_descriptions(content)
    print(f"Total description blocks: {len(descriptions)}\n")
    for i, desc in enumerate(descriptions, 1):
        print(f"{i}. {desc[:150]}...")
        print()

    # ===== GENERATE FRONTMATTER =====
    print(f"{'='*100}")
    print("GENERATED FRONTMATTER (YAML)")
    print(f"{'='*100}\n")

    print(f"---")
    print(f"title: \"{title}\"")
    print(f"date: \"{post_date}\"")
    print(f"slug: \"{post_id}\"")

    if descriptions:
        # Use first longer description as post description
        desc = descriptions[0][:200]
        desc = desc.replace('\"', '\\"')
        print(f"description: \"{desc}...\"")

    print(f"archiveStatus: \"archived\"")

    if speakers:
        print(f"speakers:")
        for speaker in speakers:
            print(f"  - name: \"{speaker['name']}\"")
            print(f"    title: \"{speaker['title']}\"")

    if topics:
        print(f"topics:")
        for topic in topics:
            print(f"  - title: \"{topic['title']}\"")
            if speakers and len(speakers) >= topic['number']:
                print(f"    speaker: \"{speakers[topic['number']-1]['name']}\"")
            if len(learning_points) > 0:
                # Distribute learning points to topics
                points_per_topic = len(learning_points) // len(topics)
                start_idx = (topic['number'] - 1) * points_per_topic
                end_idx = start_idx + points_per_topic
                if topic['number'] == len(topics):
                    end_idx = len(learning_points)
                if start_idx < len(learning_points):
                    print(f"    keyPoints:")
                    for point in learning_points[start_idx:end_idx]:
                        point = point.replace('\"', '\\"')
                        print(f"      - \"{point}\"")

    if materials:
        print(f"archiveMaterials:")
        for material in materials:
            print(f"  - type: \"{material['type']}\"")
            print(f"    url: \"{material['url']}\"")

    print(f"---\n")

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

    extract_post_correctly(target_file)

if __name__ == '__main__':
    main()
