#!/usr/bin/env python3
"""
Enhanced WordPress Meetings Migration Script (Version 2)
Converts WordPress XML export to clean Nuxt Markdown files with proper shortcode parsing

Improvements over v1:
- Parses WordPress Visual Composer shortcodes
- Extracts speaker information from [dfd_new_team_member]
- Extracts archive materials from [dfd_button]
- Extracts key learning points from [dfd_icon_list]
- Generates clean, readable Markdown
- Properly structures YAML frontmatter with extracted data
"""

import xml.etree.ElementTree as ET
import json
import os
import shutil
import logging
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote, urlparse
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedMeetingExtractor:
    """Enhanced extractor with WordPress shortcode parsing"""

    def __init__(self, xml_file_path, project_root):
        self.xml_file = xml_file_path
        self.project_root = Path(project_root)
        self.content_dir = self.project_root / 'content' / 'meetings'
        self.public_dir = self.project_root / 'public'
        self.images_meetings_dir = self.public_dir / 'images' / 'meetings'
        self.images_speakers_dir = self.public_dir / 'images' / 'speakers'
        self.documents_dir = self.public_dir / 'documents' / 'meetings'

        self.meetings = []
        self.migration_report = {
            'total_posts_processed': 0,
            'successful_migrations': 0,
            'failed_migrations': 0,
            'missing_images': [],
            'missing_pdfs': [],
            'errors': [],
            'file_mapping': {}
        }

    def setup_directories(self):
        """Create necessary directories"""
        try:
            self.content_dir.mkdir(parents=True, exist_ok=True)
            self.images_meetings_dir.mkdir(parents=True, exist_ok=True)
            self.images_speakers_dir.mkdir(parents=True, exist_ok=True)
            self.documents_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Directories created/verified")
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise

    def parse_xml(self):
        """Parse WordPress XML export file"""
        try:
            logger.info(f"Parsing XML file: {self.xml_file}")
            tree = ET.parse(self.xml_file)
            root = tree.getroot()

            namespaces = {
                'wp': 'http://wordpress.org/export/1.2/',
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'excerpt': 'http://wordpress.org/export/1.2/excerpt/'
            }

            items = root.findall('.//item')
            logger.info(f"Found {len(items)} total items in XML")

            meeting_count = 0
            for item in items:
                title_elem = item.find('title')
                title = title_elem.text if title_elem is not None else ''

                if title and 'ARCHIVE' in title.upper():
                    post_type_elem = item.find('wp:post_type', namespaces)
                    post_type = post_type_elem.text if post_type_elem is not None else ''

                    if post_type == 'post':
                        try:
                            post_data = self._extract_post_data(item, namespaces)
                            if post_data:
                                self.meetings.append(post_data)
                                meeting_count += 1
                                logger.info(f"Extracted meeting {meeting_count}: {post_data.get('title')}")
                        except Exception as e:
                            logger.error(f"Error extracting post '{title}': {e}")
                            self.migration_report['errors'].append(f"Error extracting '{title}': {str(e)}")

            logger.info(f"Successfully extracted {meeting_count} meeting archive posts")
            self.migration_report['total_posts_processed'] = meeting_count

        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            raise

    def _extract_post_data(self, item, namespaces):
        """Extract data from WordPress post"""
        post_data = {}

        title_elem = item.find('title')
        post_data['title'] = title_elem.text if title_elem is not None else 'Untitled'

        link_elem = item.find('link')
        post_data['link'] = link_elem.text if link_elem is not None else ''

        content_elem = item.find('content:encoded', namespaces)
        post_data['content'] = content_elem.text if content_elem is not None else ''

        post_id_elem = item.find('wp:post_id', namespaces)
        post_data['post_id'] = post_id_elem.text if post_id_elem is not None else ''

        post_date_elem = item.find('wp:post_date_gmt', namespaces)
        post_data['post_date_gmt'] = post_date_elem.text if post_date_elem is not None else ''

        post_name_elem = item.find('wp:post_name', namespaces)
        post_data['post_name'] = post_name_elem.text if post_name_elem is not None else self._slugify(post_data['title'])

        description_elem = item.find('description')
        post_data['description'] = description_elem.text if description_elem is not None else ''

        creator_elem = item.find('dc:creator', namespaces)
        post_data['author'] = creator_elem.text if creator_elem is not None else 'AAIILA'

        return post_data

    def _slugify(self, text):
        """Convert text to URL-friendly slug"""
        slug = re.sub(r'[^\w\s-]', '', text).lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def process_meetings(self):
        """Process meetings and generate markdown files"""
        logger.info("Starting enhanced meeting processing...")

        for meeting in self.meetings:
            try:
                # Parse content with shortcode extraction
                meeting_details = self._parse_meeting_content_advanced(meeting.get('content', ''))

                # Generate markdown file
                markdown_file = self._generate_clean_markdown(meeting, meeting_details)

                if markdown_file:
                    self.migration_report['successful_migrations'] += 1
                    self.migration_report['file_mapping'][meeting.get('post_id', '')] = markdown_file
                    logger.info(f"Successfully processed: {markdown_file}")
                else:
                    self.migration_report['failed_migrations'] += 1

            except Exception as e:
                logger.error(f"Error processing meeting '{meeting.get('title')}': {e}")
                self.migration_report['failed_migrations'] += 1
                self.migration_report['errors'].append(f"Error processing '{meeting.get('title')}': {str(e)}")

    def _parse_meeting_content_advanced(self, html_content):
        """Advanced parser for WordPress shortcodes"""
        details = {
            'meeting_date': '',
            'topics': [],
            'archive_materials': []
        }

        # Extract meeting date
        date_match = re.search(r'(?:Saturday|Sunday|Monday|Tuesday|Wednesday|Thursday|Friday)[,\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})', html_content)
        if date_match:
            details['meeting_date'] = date_match.group(1)

        # Parse topics with speaker information
        topics = self._extract_topics_from_shortcodes(html_content)
        details['topics'] = topics

        # Parse archive materials
        materials = self._extract_archive_materials(html_content)
        details['archive_materials'] = materials

        return details

    def _extract_topics_from_shortcodes(self, html_content):
        """Extract topics from dfd_heading and dfd_new_team_member shortcodes"""
        topics = []

        # Find all TOPIC sections
        topic_pattern = r'\[dfd_heading[^\]]*\].*?TOPIC\s+(\d+).*?\[/dfd_heading\]'
        topic_matches = list(re.finditer(topic_pattern, html_content, re.IGNORECASE | re.DOTALL))

        for i, topic_match in enumerate(topic_matches):
            topic_num = topic_match.group(1)
            topic_start = topic_match.end()

            # Find the next topic or end of content
            if i + 1 < len(topic_matches):
                topic_end = topic_matches[i + 1].start()
            else:
                topic_end = len(html_content)

            topic_section = html_content[topic_start:topic_end]

            # Extract speaker info from dfd_new_team_member
            speaker_info = self._extract_speaker_from_shortcode(topic_section)

            # Extract topic title and description
            title_match = re.search(r'\[dfd_heading[^\]]*\]([^[]*)\[/dfd_heading\]', topic_section, re.IGNORECASE)
            topic_title = title_match.group(1).strip() if title_match else f"Topic {topic_num}"

            # Extract topic description
            description = self._extract_topic_description(topic_section)

            # Extract key learning points
            key_points = self._extract_key_points(topic_section)

            topic = {
                'title': topic_title,
                'speaker': speaker_info.get('name', ''),
                'speakerTitle': speaker_info.get('title', ''),
                'speakerImage': speaker_info.get('image', ''),
                'description': description,
                'keyPoints': key_points
            }
            topics.append(topic)
            logger.info(f"Extracted topic {topic_num}: {topic_title}")

        return topics

    def _extract_speaker_from_shortcode(self, content):
        """Extract speaker name and title from dfd_new_team_member shortcode"""
        speaker_info = {'name': '', 'title': '', 'image': ''}

        # Parse dfd_new_team_member shortcode
        speaker_match = re.search(r'\[dfd_new_team_member[^\]]*?team_member_name="([^"]*)"[^\]]*?team_member_job_position="([^"]*)"[^\]]*?\]', content)
        if speaker_match:
            speaker_info['name'] = speaker_match.group(1).strip()
            speaker_info['title'] = speaker_match.group(2).strip()

            # Extract speaker photo ID and convert to filename
            photo_match = re.search(r'team_member_photo="(\d+)"', content)
            if photo_match:
                photo_id = photo_match.group(1)
                # Try to find the actual filename for this photo ID
                speaker_info['image'] = f"/images/speakers/speaker-{photo_id}.jpg"

        return speaker_info

    def _extract_topic_description(self, content):
        """Extract topic description from content"""
        # Look for text between heading and archive materials or next topic
        # Remove shortcode markup and extract clean text
        text = re.sub(r'\[dfd_heading[^\]]*\].*?\[/dfd_heading\]', '', content, flags=re.DOTALL)
        text = re.sub(r'\[dfd_new_team_member[^\]]*\]', '', text)
        text = re.sub(r'\[vc_column_text\]', '', text)
        text = re.sub(r'\[/vc_column_text\]', '\n', text)

        # Extract first substantial paragraph
        paragraphs = re.split(r'\n\n+', text.strip())
        for para in paragraphs:
            para = para.strip()
            # Skip empty, very short, or shortcode-only content
            if len(para) > 50 and '[' not in para and not para.startswith('You will learn'):
                return para[:500]  # Limit to 500 chars

        return ''

    def _extract_key_points(self, content):
        """Extract learning points from dfd_icon_list shortcode"""
        key_points = []

        # Find dfd_icon_list shortcode
        icon_list_match = re.search(r'\[dfd_icon_list[^\]]*list_fields="([^"]*)"', content)
        if icon_list_match:
            list_fields = unquote(icon_list_match.group(1))
            # Parse URL-encoded JSON
            try:
                # Replace %5B with [ and %5D with ] for JSON array
                list_fields = list_fields.replace('%5B', '[').replace('%5D', ']')
                list_fields = list_fields.replace('%22', '"')
                list_data = json.loads(list_fields)

                for item in list_data:
                    if 'text_content' in item:
                        point = item['text_content']
                        # Clean up URL encoding
                        point = unquote(point)
                        # Remove line breaks
                        point = point.replace('\n', ' ').strip()
                        if point:
                            key_points.append(point)
            except Exception as e:
                logger.warning(f"Could not parse icon list: {e}")

        return key_points

    def _extract_archive_materials(self, html_content):
        """Extract archive materials from dfd_button shortcodes"""
        materials = []

        # Find all dfd_button shortcodes
        button_pattern = r'\[dfd_button[^\]]*button_text="([^"]*)"[^\]]*buttom_link_src="url:([^|"]*)[^"]*"\]'
        button_matches = re.finditer(button_pattern, html_content)

        for match in button_matches:
            button_text = match.group(1).strip()
            url = unquote(match.group(2)).strip()

            if not url or url == 'url:':
                continue

            # Determine material type
            if 'recording' in button_text.lower() or 'video' in button_text.lower():
                material_type = 'Recording'
            elif 'pdf' in button_text.lower() or 'slides' in button_text.lower() or url.endswith('.pdf'):
                material_type = 'PDF'
            else:
                material_type = 'Document'

            material = {
                'type': material_type,
                'title': button_text,
                'url': url
            }
            materials.append(material)
            logger.info(f"Extracted material: {button_text} ({material_type})")

        return materials

    def _escape_yaml_string(self, s):
        """Escape special characters in YAML strings"""
        if not s:
            return ''
        s = str(s).replace('\\', '\\\\').replace('"', '\\"')
        return s

    def _generate_clean_markdown(self, meeting, details):
        """Generate clean markdown file from extracted data"""
        try:
            slug = meeting.get('post_name', self._slugify(meeting.get('title', 'meeting')))
            date_str = meeting.get('post_date_gmt', '')

            try:
                date_parts = date_str.split()[0] if date_str else ''
            except:
                date_parts = ''

            # Build frontmatter
            yaml_lines = ['---']
            yaml_lines.append(f'title: "{self._escape_yaml_string(meeting["title"])}"')
            yaml_lines.append(f'description: "{self._escape_yaml_string(meeting.get("description", ""))}"')
            yaml_lines.append(f'date: "{date_parts or datetime.now().strftime("%Y-%m-%d")}"')
            yaml_lines.append(f'image: "/images/meetings/placeholder.jpg"')
            yaml_lines.append(f'archiveStatus: "archived"')
            yaml_lines.append(f'slug: "{slug}"')
            yaml_lines.append(f'author: "{self._escape_yaml_string(meeting.get("author", "AAIILA"))}"')

            # Add topics
            if details.get('topics'):
                yaml_lines.append('topics:')
                for topic in details['topics']:
                    yaml_lines.append(f'  - title: "{self._escape_yaml_string(topic.get("title", ""))}"')
                    yaml_lines.append(f'    speaker: "{self._escape_yaml_string(topic.get("speaker", ""))}"')
                    yaml_lines.append(f'    speakerTitle: "{self._escape_yaml_string(topic.get("speakerTitle", ""))}"')
                    yaml_lines.append(f'    speakerImage: "{self._escape_yaml_string(topic.get("speakerImage", ""))}"')
                    yaml_lines.append(f'    description: "{self._escape_yaml_string(topic.get("description", ""))}"')
                    yaml_lines.append('    keyPoints:')
                    for point in topic.get('keyPoints', []):
                        yaml_lines.append(f'      - "{self._escape_yaml_string(point)}"')

            # Add archive materials
            if details.get('archive_materials'):
                yaml_lines.append('archiveMaterials:')
                for material in details['archive_materials']:
                    yaml_lines.append(f'  - type: "{self._escape_yaml_string(material.get("type", ""))}"')
                    yaml_lines.append(f'    title: "{self._escape_yaml_string(material.get("title", ""))}"')
                    yaml_lines.append(f'    url: "{self._escape_yaml_string(material.get("url", ""))}"')

            yaml_lines.append('---')

            # Build markdown body
            body_lines = []
            if details.get('meeting_date'):
                body_lines.append(f"## {details['meeting_date']}\n")

            body_lines.append("THIS IS AN ARCHIVED PRESENTATION\n")

            if details.get('topics'):
                body_lines.append("## Program Information\n")
                for i, topic in enumerate(details['topics'], 1):
                    body_lines.append(f"### Topic {i}: {topic.get('title', 'Unknown')}\n")
                    if topic.get('speaker'):
                        body_lines.append(f"**Speaker:** {topic['speaker']}\n")
                    if topic.get('speakerTitle'):
                        body_lines.append(f"**Title:** {topic['speakerTitle']}\n")
                    if topic.get('description'):
                        body_lines.append(f"{topic['description']}\n")
                    if topic.get('keyPoints'):
                        body_lines.append("**Key Learning Points:**\n")
                        for point in topic['keyPoints']:
                            body_lines.append(f"- {point}\n")
                    body_lines.append("")

            body = '\n'.join(body_lines).strip()

            # Combine frontmatter and body
            full_content = '\n'.join(yaml_lines) + '\n\n' + body

            # Write file
            filename = f"{slug}.md"
            filepath = self.content_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)

            logger.info(f"Generated clean markdown: {filepath}")
            return filename

        except Exception as e:
            logger.error(f"Error generating markdown for '{meeting.get('title')}': {e}")
            return None

    def generate_report(self):
        """Generate migration report"""
        report_path = self.project_root / 'migration-report-v2.md'

        report_content = f"""# WordPress Meetings Migration Report (Enhanced v2)

## Summary
- **Total Posts Processed:** {self.migration_report['total_posts_processed']}
- **Successful Migrations:** {self.migration_report['successful_migrations']}
- **Failed Migrations:** {self.migration_report['failed_migrations']}
- **Migration Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Key Improvements
- ✅ Enhanced WordPress shortcode parsing
- ✅ Proper extraction of speaker information
- ✅ Clean Markdown generation (no shortcodes)
- ✅ Structured data in YAML frontmatter

## File Mapping
WordPress Post ID → Markdown Filename

"""
        for post_id, filename in self.migration_report['file_mapping'].items():
            report_content += f"- `{post_id}` → `{filename}`\n"

        if self.migration_report['errors']:
            report_content += "\n## Errors Encountered\n\n"
            for error in self.migration_report['errors'][:20]:
                report_content += f"- {error}\n"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Enhanced migration report generated: {report_path}")

    def run(self):
        """Execute complete migration"""
        try:
            logger.info("=" * 70)
            logger.info("Enhanced WordPress Meetings Migration Started (v2)")
            logger.info("=" * 70)

            self.setup_directories()
            self.parse_xml()
            self.process_meetings()
            self.generate_report()

            logger.info("=" * 70)
            logger.info("Enhanced WordPress Meetings Migration Completed Successfully")
            logger.info("=" * 70)

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False


def main():
    """Main entry point"""
    PROJECT_ROOT = Path(__file__).parent.parent
    XML_FILE = PROJECT_ROOT / 'AAII-Migration-assets' / 'aaiilaorg.WordPress.2025-07-27 (1).xml'

    if not XML_FILE.exists():
        logger.error(f"XML file not found: {XML_FILE}")
        return 1

    extractor = EnhancedMeetingExtractor(str(XML_FILE), PROJECT_ROOT)
    success = extractor.run()

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
