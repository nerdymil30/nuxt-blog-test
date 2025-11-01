#!/usr/bin/env python3
"""
WordPress to Nuxt Migration - Version 3 (Corrected Extraction)
Migrates meeting archive posts to Markdown with proper parsing of:
- Topic titles (not labels)
- Speaker information (deduplicated)
- Archive materials (with clean URLs)
- Learning points (from JSON)
- Descriptions (from column text blocks)
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re
import json
from urllib.parse import unquote
import html
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
INDIVIDUAL_POSTS_DIR = PROJECT_ROOT / 'AAII-Migration-assets' / 'individual-posts'
OUTPUT_DIR = PROJECT_ROOT / 'content' / 'meetings'
PUBLIC_IMAGES_DIR = PROJECT_ROOT / 'public' / 'images' / 'meetings'
PUBLIC_SPEAKERS_DIR = PROJECT_ROOT / 'public' / 'images' / 'speakers'
PUBLIC_DOCS_DIR = PROJECT_ROOT / 'public' / 'documents' / 'meetings'

class MeetingMigrator:
    """Migrates meeting posts from individual XML files to Markdown"""

    def __init__(self):
        self.namespaces = {
            'wp': 'http://wordpress.org/export/1.2/',
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'dc': 'http://purl.org/dc/elements/1.1/',
        }
        self.stats = {
            'total_posts': 0,
            'migrated': 0,
            'errors': 0,
            'total_topics': 0,
            'total_speakers': 0,
            'total_materials': 0,
        }

    def setup_directories(self):
        """Create output directories"""
        for dir_path in [OUTPUT_DIR, PUBLIC_IMAGES_DIR, PUBLIC_SPEAKERS_DIR, PUBLIC_DOCS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created output directories")

    def get_text(self, element):
        """Safely get text from XML element"""
        if element is None:
            return ""
        return element.text or ""

    def extract_topics_correct(self, content):
        """Extract topics with correct pairing of labels and titles"""
        topics = []

        # Find all [dfd_heading] tags with content
        heading_matches = list(re.finditer(
            r'\[dfd_heading[^\]]*\]([^[]*)\[/dfd_heading\]',
            content,
            re.IGNORECASE | re.DOTALL
        ))

        headings = [m.group(1).strip() for m in heading_matches]

        # Find TOPIC N labels and pair with following heading
        topic_num = 1
        for i, heading_text in enumerate(headings):
            if f"TOPIC {topic_num}" in heading_text.upper():
                # Next heading should be the actual title
                if i + 1 < len(headings):
                    actual_title = headings[i + 1]
                    # Make sure it's not another TOPIC label
                    if "TOPIC" not in actual_title.upper():
                        topics.append({
                            'number': topic_num,
                            'title': actual_title
                        })
                        topic_num += 1

        return topics

    def extract_speakers_correct(self, content):
        """Extract speakers with proper parsing and deduplication"""
        speakers = []
        seen_speakers = set()

        # Find all [dfd_new_team_member ...] shortcodes
        speaker_matches = re.finditer(
            r'\[dfd_new_team_member\s+([^\]]*)\]',
            content,
            re.IGNORECASE | re.DOTALL
        )

        for match in speaker_matches:
            attrs_str = match.group(1)

            # Extract key="value" attributes
            params = {}
            for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
                key = attr_match.group(1)
                value = attr_match.group(2)
                # Unescape URL encoding and HTML entities
                try:
                    value = unquote(value)
                except:
                    pass
                value = html.unescape(value)
                params[key] = value

            name = params.get('team_member_name', '').strip()
            title = params.get('team_member_job_position', '').strip()
            image = params.get('team_member_image', '').strip()

            # Skip duplicates
            speaker_key = (name, title)
            if speaker_key not in seen_speakers:
                speakers.append({
                    'name': name,
                    'title': title,
                    'image': image
                })
                seen_speakers.add(speaker_key)

        return speakers

    def extract_archive_materials_correct(self, content):
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

            # Extract and clean buttom_link_src
            link_match = re.search(r'buttom_link_src="([^"]*)"', attrs)
            if link_match:
                button_link = link_match.group(1)

                # Extract URL from "url:..." format and remove trailing ||...
                url_match = re.search(r'url:([^|]*)', button_link)
                if url_match:
                    url = url_match.group(1).strip()
                    # URL decode and unescape
                    url = unquote(url)
                    url = html.unescape(url)

                    materials.append({
                        'type': button_text,
                        'url': url
                    })

        return materials

    def extract_learning_points_correct(self, content):
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

    def extract_speaker_descriptions(self, content):
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

            # Remove HTML tags
            text_no_tags = re.sub(r'<[^>]*>', '', text_clean)
            text_no_tags = html.unescape(text_no_tags).strip()

            # Filter for actual descriptions (has length, not a header)
            if len(text_no_tags) > 50 and not re.match(r'^(PROGRAM|ARCHIVE|Attend)', text_no_tags):
                descriptions.append(text_no_tags)

        return descriptions

    def escape_yaml_string(self, text):
        """Escape string for YAML frontmatter"""
        if not text:
            return ""
        # Escape quotes and backslashes
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        return text

    def generate_markdown_content(self, post_data):
        """Generate markdown content with proper frontmatter"""
        lines = ['---']

        # Basic fields
        lines.append(f'title: "{self.escape_yaml_string(post_data["title"])}"')
        lines.append(f'date: "{post_data["date"]}"')
        lines.append(f'slug: "{post_data["slug"]}"')

        # Description (first longer description)
        if post_data['descriptions']:
            desc = post_data['descriptions'][0][:200]
            lines.append(f'description: "{self.escape_yaml_string(desc)}..."')

        lines.append(f'archiveStatus: "archived"')

        # Speakers
        if post_data['speakers']:
            lines.append('speakers:')
            for speaker in post_data['speakers']:
                lines.append(f'  - name: "{self.escape_yaml_string(speaker["name"])}"')
                lines.append(f'    title: "{self.escape_yaml_string(speaker["title"])}"')

        # Topics with learning points
        if post_data['topics']:
            lines.append('topics:')
            for topic in post_data['topics']:
                lines.append(f'  - title: "{self.escape_yaml_string(topic["title"])}"')

                # Match speaker to topic (by index)
                if post_data['speakers'] and topic['number'] - 1 < len(post_data['speakers']):
                    speaker_name = post_data['speakers'][topic['number'] - 1]['name']
                    lines.append(f'    speaker: "{self.escape_yaml_string(speaker_name)}"')

                # Distribute learning points to topics
                if post_data['learning_points']:
                    points_per_topic = len(post_data['learning_points']) // len(post_data['topics'])
                    start_idx = (topic['number'] - 1) * points_per_topic
                    end_idx = start_idx + points_per_topic
                    if topic['number'] == len(post_data['topics']):
                        end_idx = len(post_data['learning_points'])

                    if start_idx < len(post_data['learning_points']):
                        lines.append('    keyPoints:')
                        for point in post_data['learning_points'][start_idx:end_idx]:
                            lines.append(f'      - "{self.escape_yaml_string(point)}"')

        # Archive materials
        if post_data['materials']:
            lines.append('archiveMaterials:')
            for material in post_data['materials']:
                lines.append(f'  - type: "{self.escape_yaml_string(material["type"])}"')
                lines.append(f'    url: "{material["url"]}"')

        lines.append('---')
        lines.append('')
        lines.append(post_data['body'])

        return '\n'.join(lines)

    def migrate_post(self, xml_file_path):
        """Migrate a single post from XML to Markdown"""

        try:
            # Parse XML
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Extract basic info
            title = self.get_text(root.find('title'))
            post_id = self.get_text(root.find('wp:post_id', self.namespaces))
            post_date = self.get_text(root.find('wp:post_date_gmt', self.namespaces))
            content = self.get_text(root.find('content:encoded', self.namespaces))

            if not title or not content:
                return False

            # Extract structured data
            topics = self.extract_topics_correct(content)
            speakers = self.extract_speakers_correct(content)
            materials = self.extract_archive_materials_correct(content)
            learning_points = self.extract_learning_points_correct(content)
            descriptions = self.extract_speaker_descriptions(content)

            # Build post data
            post_data = {
                'title': title,
                'slug': post_id,
                'date': post_date,
                'topics': topics,
                'speakers': speakers,
                'materials': materials,
                'learning_points': learning_points,
                'descriptions': descriptions,
                'body': 'Meeting archive page.\n\n**Topics covered:**\n\n' +
                        '\n\n'.join([f"- {t['title']}" for t in topics]) if topics else 'No topics found.'
            }

            # Generate markdown
            markdown_content = self.generate_markdown_content(post_data)

            # Generate filename (sanitized title or use ID)
            if len(title) > 50:
                filename = f"{post_id}.md"
            else:
                # Sanitize title for filename
                safe_title = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                filename = f"{safe_title}-{post_id}.md"

            # Write markdown file
            output_path = OUTPUT_DIR / filename
            output_path.write_text(markdown_content, encoding='utf-8')

            # Update stats
            self.stats['migrated'] += 1
            self.stats['total_topics'] += len(topics)
            self.stats['total_speakers'] += len(speakers)
            self.stats['total_materials'] += len(materials)

            return True

        except Exception as e:
            print(f"ERROR processing {xml_file_path.name}: {e}")
            self.stats['errors'] += 1
            return False

    def run(self):
        """Run migration on all individual XML files"""

        print(f"{'='*100}")
        print("WORDPRESS MIGRATION v3 (CORRECTED EXTRACTION)")
        print(f"{'='*100}\n")

        # Setup
        self.setup_directories()

        # Find all XML files
        xml_files = sorted(INDIVIDUAL_POSTS_DIR.glob('*.xml'))
        self.stats['total_posts'] = len(xml_files)

        print(f"Found {len(xml_files)} posts to migrate\n")
        print(f"{'='*100}")
        print("MIGRATING...")
        print(f"{'='*100}\n")

        # Migrate each post
        for i, xml_file in enumerate(xml_files, 1):
            success = self.migrate_post(xml_file)
            status = "✓" if success else "✗"
            print(f"{i:3d}. {status} {xml_file.name}")

        # Report
        print(f"\n{'='*100}")
        print("MIGRATION COMPLETE")
        print(f"{'='*100}\n")
        print(f"Total posts:         {self.stats['total_posts']}")
        print(f"Successfully migrated: {self.stats['migrated']}")
        print(f"Errors:              {self.stats['errors']}")
        print(f"Total topics:        {self.stats['total_topics']}")
        print(f"Total speakers:      {self.stats['total_speakers']}")
        print(f"Total materials:     {self.stats['total_materials']}")
        print(f"\nOutput directory: {OUTPUT_DIR}")
        print(f"Output files: {len(list(OUTPUT_DIR.glob('*.md')))}")

def main():
    """Entry point"""
    migrator = MeetingMigrator()
    migrator.run()

if __name__ == '__main__':
    main()
