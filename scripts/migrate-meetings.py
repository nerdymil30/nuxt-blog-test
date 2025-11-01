#!/usr/bin/env python3
"""
WordPress Meetings Archive Migration Script
Converts WordPress XML export to Nuxt Markdown files with YAML frontmatter

This script:
1. Parses WordPress XML export file
2. Extracts meeting archive posts
3. Parses HTML content to extract topics, speakers, and learning points
4. Generates Markdown files with proper frontmatter
5. Organizes and copies assets (images, PDFs)
6. Generates migration report
"""

import xml.etree.ElementTree as ET
import json
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlparse
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MeetingExtractor:
    """Extract and process WordPress meeting posts from XML export"""

    def __init__(self, xml_file_path, project_root):
        """
        Initialize the extractor

        Args:
            xml_file_path: Path to WordPress XML export file
            project_root: Root directory of Nuxt project
        """
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
            'file_mapping': {},
            'assets_organized': []
        }

    def setup_directories(self):
        """Create necessary directories"""
        try:
            self.content_dir.mkdir(parents=True, exist_ok=True)
            self.images_meetings_dir.mkdir(parents=True, exist_ok=True)
            self.images_speakers_dir.mkdir(parents=True, exist_ok=True)
            self.documents_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directories created/verified")
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise

    def parse_xml(self):
        """Parse WordPress XML export file and extract meeting posts"""
        try:
            logger.info(f"Parsing XML file: {self.xml_file}")
            tree = ET.parse(self.xml_file)
            root = tree.getroot()

            # Define XML namespaces
            namespaces = {
                'wp': 'http://wordpress.org/export/1.2/',
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'excerpt': 'http://wordpress.org/export/1.2/excerpt/'
            }

            # Find all items (posts)
            items = root.findall('.//item')
            logger.info(f"Found {len(items)} total items in XML")

            # Filter for meeting archive posts (those with "ARCHIVE" in title)
            meeting_count = 0
            for item in items:
                title_elem = item.find('title')
                title = title_elem.text if title_elem is not None else ''

                # Check if this is an archive post
                if title and 'ARCHIVE' in title.upper():
                    post_type_elem = item.find('wp:post_type', namespaces)
                    post_type = post_type_elem.text if post_type_elem is not None else ''

                    # Only process posts, not attachments
                    if post_type == 'post':
                        try:
                            post_data = self._extract_post_data(item, namespaces)
                            if post_data:
                                self.meetings.append(post_data)
                                meeting_count += 1
                                logger.info(f"Extracted meeting {meeting_count}: {post_data.get('title', 'Unknown')}")
                        except Exception as e:
                            logger.error(f"Error extracting post '{title}': {e}")
                            self.migration_report['errors'].append(f"Error extracting '{title}': {str(e)}")

            logger.info(f"Successfully extracted {meeting_count} meeting archive posts")
            self.migration_report['total_posts_processed'] = meeting_count

        except ET.ParseError as e:
            logger.error(f"XML Parse Error: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"XML file not found: {self.xml_file}")
            raise

    def _extract_post_data(self, item, namespaces):
        """Extract data from a single WordPress post item"""
        post_data = {}

        # Extract basic fields
        title_elem = item.find('title')
        post_data['title'] = title_elem.text if title_elem is not None else 'Untitled'

        link_elem = item.find('link')
        post_data['link'] = link_elem.text if link_elem is not None else ''

        content_elem = item.find('content:encoded', namespaces)
        post_data['content'] = content_elem.text if content_elem is not None else ''

        # Extract post metadata
        post_id_elem = item.find('wp:post_id', namespaces)
        post_data['post_id'] = post_id_elem.text if post_id_elem is not None else ''

        post_date_elem = item.find('wp:post_date_gmt', namespaces)
        post_data['post_date_gmt'] = post_date_elem.text if post_date_elem is not None else ''

        post_name_elem = item.find('wp:post_name', namespaces)
        post_data['post_name'] = post_name_elem.text if post_name_elem is not None else self._slugify(post_data['title'])

        # Extract description/excerpt
        description_elem = item.find('description')
        post_data['description'] = description_elem.text if description_elem is not None else ''

        # Extract creator/author
        creator_elem = item.find('dc:creator', namespaces)
        post_data['author'] = creator_elem.text if creator_elem is not None else 'AAIILA'

        # Find featured image (post_parent = 0 indicates post, not attachment)
        post_data['featured_image'] = self._find_featured_image(item, namespaces)

        return post_data

    def _find_featured_image(self, item, namespaces):
        """Find featured image URL for a post"""
        # Look for post meta containing featured image ID
        post_meta_list = item.findall('wp:postmeta', namespaces)
        for meta in post_meta_list:
            meta_key = meta.find('wp:meta_key', namespaces)
            meta_value = meta.find('wp:meta_value', namespaces)

            if meta_key is not None and meta_key.text == '_thumbnail_id' and meta_value is not None:
                # This references an image post ID, but we'll handle image extraction differently
                return None

        # Alternative: look in post content for first image
        if item.find('content:encoded', namespaces) is not None:
            content = item.find('content:encoded', namespaces).text or ''
            # Extract first image URL from content
            img_pattern = r'<img[^>]+src="([^"]+)"'
            matches = re.findall(img_pattern, content)
            if matches:
                return matches[0]

        return None

    def _slugify(self, text):
        """Convert text to URL-friendly slug"""
        # Convert to lowercase, replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', text).lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def process_meetings(self):
        """Process extracted meetings to generate Markdown files"""
        logger.info("Starting meeting processing...")

        for meeting in self.meetings:
            try:
                # Parse content to extract structured data
                meeting_details = self._parse_meeting_content(meeting)

                # Generate Markdown file
                markdown_file = self._generate_markdown_file(meeting, meeting_details)

                if markdown_file:
                    self.migration_report['successful_migrations'] += 1
                    self.migration_report['file_mapping'][meeting.get('post_id', '')] = markdown_file
                    logger.info(f"Successfully processed: {markdown_file}")
                else:
                    self.migration_report['failed_migrations'] += 1

            except Exception as e:
                logger.error(f"Error processing meeting '{meeting.get('title', 'Unknown')}': {e}")
                self.migration_report['failed_migrations'] += 1
                self.migration_report['errors'].append(f"Error processing '{meeting.get('title')}': {str(e)}")

        logger.info(f"Processing complete: {self.migration_report['successful_migrations']} successful, "
                   f"{self.migration_report['failed_migrations']} failed")

    def _parse_meeting_content(self, meeting):
        """Parse HTML content to extract topics, speakers, and learning points"""
        details = {
            'topics': [],
            'archive_materials': []
        }

        content = meeting.get('content', '')
        if not content:
            logger.warning(f"No content found for meeting: {meeting.get('title')}")
            return details

        # Extract topics and speakers
        # This is a simplified parser - real implementation would need more sophisticated HTML parsing
        topics = self._extract_topics(content)
        details['topics'] = topics

        # Extract archive materials (PDFs, recordings)
        materials = self._extract_archive_materials(content)
        details['archive_materials'] = materials

        return details

    def _extract_topics(self, html_content):
        """Extract topics from HTML content"""
        topics = []

        # Split content into sections by TOPIC patterns
        # Look for patterns like "TOPIC 1", "TOPIC 2", etc.
        topic_sections = re.split(r'<h[2-4][^>]*>\s*TOPIC\s+(\d+)', html_content, flags=re.IGNORECASE)

        # First element is content before first topic, skip it
        for i in range(1, len(topic_sections), 2):
            if i + 1 < len(topic_sections):
                topic_num = topic_sections[i]
                topic_content = topic_sections[i + 1]

                # Extract topic title (first heading in section)
                title_match = re.search(r'<h[2-4][^>]*>([^<]+)</h[2-4]>', topic_content, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else f'Topic {topic_num}'

                # Extract speaker info
                speaker = ''
                speaker_title = ''
                speaker_image = ''

                # Look for speaker name pattern (usually bold or in specific format)
                speaker_match = re.search(r'<strong>([^<]+)</strong>\s*(?:<br\s*/?>\s*)?<em>([^<]+)</em>|<strong>([^<]+)</strong>', topic_content, re.IGNORECASE)
                if speaker_match:
                    speaker = speaker_match.group(1) or speaker_match.group(3) or ''
                    speaker_title = speaker_match.group(2) or ''

                # Look for speaker image
                img_match = re.search(r'<img[^>]+src="([^"]*speaker[^"]*|[^"]*-[0-9]+x[0-9]+\.jpg)"[^>]*>', topic_content, re.IGNORECASE)
                if img_match:
                    speaker_image = img_match.group(1)

                # Extract description (first paragraph or text before learning points)
                description_match = re.search(r'<p[^>]*>([^<]+)</p>', topic_content, re.IGNORECASE)
                description = description_match.group(1).strip() if description_match else ''

                # Extract key learning points (usually in specific format)
                key_points = []
                # Look for "Learn" or similar headers with bullets
                points_match = re.search(r'(?:Learn|Key Points?|You will learn|Objectives?).*?(?:<ul>|<ol>)(.*?)(?:</ul>|</ol>)', topic_content, re.IGNORECASE | re.DOTALL)
                if points_match:
                    bullets = re.findall(r'<li[^>]*>([^<]+)</li>', points_match.group(1), re.IGNORECASE)
                    key_points = [re.sub(r'<[^>]+>', '', bullet).strip() for bullet in bullets]

                topic = {
                    'title': title,
                    'speaker': speaker.strip(),
                    'speakerTitle': speaker_title.strip(),
                    'speakerImage': speaker_image,
                    'description': description,
                    'keyPoints': key_points
                }
                topics.append(topic)
                logger.info(f"Extracted topic {topic_num}: {title}")

        # If no topics found, create empty topics list
        if not topics:
            logger.warning("No topics found in content with detailed parsing")

        return topics

    def _extract_archive_materials(self, html_content):
        """Extract PDF and recording links from content"""
        materials = []

        # Look for PDF links
        pdf_pattern = r'<a[^>]+href="([^"]+\.pdf)"[^>]*>([^<]+)</a>'
        pdf_matches = re.finditer(pdf_pattern, html_content, re.IGNORECASE)

        for match in pdf_matches:
            url = match.group(1)
            title = match.group(2).strip()
            materials.append({
                'type': 'PDF',
                'title': title or 'Meeting Slides',
                'url': url
            })

        # Look for recording links (common platforms)
        recording_pattern = r'<a[^>]+href="(https?://(?:vimeo\.com|youtu(?:be)?\.com|zoom\.us)[^"]+)"[^>]*>([^<]+)</a>'
        recording_matches = re.finditer(recording_pattern, html_content, re.IGNORECASE)

        for match in recording_matches:
            url = match.group(1)
            title = match.group(2).strip()
            materials.append({
                'type': 'Recording',
                'title': title or 'Webinar Recording',
                'url': url
            })

        return materials

    def _escape_yaml_string(self, s):
        """Escape special characters in YAML strings"""
        if not s:
            return ''
        # Escape backslashes first, then quotes
        s = str(s).replace('\\', '\\\\').replace('"', '\\"')
        return s

    def _generate_markdown_file(self, meeting, details):
        """Generate Markdown file with YAML frontmatter"""
        try:
            # Prepare frontmatter data
            slug = meeting.get('post_name', self._slugify(meeting.get('title', 'meeting')))

            # Parse date
            date_str = meeting.get('post_date_gmt', '')
            try:
                # Convert "2025-07-23 18:25:18" format to "2025-07-23"
                date_parts = date_str.split()[0] if date_str else ''
            except:
                date_parts = ''

            # Build frontmatter
            frontmatter = {
                'title': meeting.get('title', 'Untitled Meeting'),
                'description': meeting.get('description', ''),
                'date': date_parts or datetime.now().strftime('%Y-%m-%d'),
                'image': '/images/meetings/placeholder.jpg',  # Will be updated by asset organization
                'archiveStatus': 'archived',
                'slug': slug,
                'author': meeting.get('author', 'AAIILA'),
                'topics': details.get('topics', []),
                'archiveMaterials': details.get('archive_materials', [])
            }

            # Generate YAML frontmatter
            yaml_lines = ['---']
            yaml_lines.append(f'title: "{self._escape_yaml_string(frontmatter["title"])}"')
            yaml_lines.append(f'description: "{self._escape_yaml_string(frontmatter["description"])}"')
            yaml_lines.append(f'date: "{frontmatter["date"]}"')
            yaml_lines.append(f'image: "{frontmatter["image"]}"')
            yaml_lines.append(f'archiveStatus: "{frontmatter["archiveStatus"]}"')
            yaml_lines.append(f'slug: "{frontmatter["slug"]}"')
            yaml_lines.append(f'author: "{self._escape_yaml_string(frontmatter["author"])}"')

            # Add topics array
            if frontmatter['topics']:
                yaml_lines.append('topics:')
                for topic in frontmatter['topics']:
                    yaml_lines.append(f'  - title: "{self._escape_yaml_string(topic.get("title", ""))}"')
                    yaml_lines.append(f'    speaker: "{self._escape_yaml_string(topic.get("speaker", ""))}"')
                    yaml_lines.append(f'    speakerTitle: "{self._escape_yaml_string(topic.get("speakerTitle", ""))}"')
                    yaml_lines.append(f'    speakerImage: "{self._escape_yaml_string(topic.get("speakerImage", ""))}"')
                    description = self._escape_yaml_string(topic.get("description", ""))
                    yaml_lines.append(f'    description: "{description}"')
                    yaml_lines.append('    keyPoints:')
                    for point in topic.get('keyPoints', []):
                        yaml_lines.append(f'      - "{self._escape_yaml_string(point)}"')

            # Add archive materials array
            if frontmatter['archiveMaterials']:
                yaml_lines.append('archiveMaterials:')
                for material in frontmatter['archiveMaterials']:
                    yaml_lines.append(f'  - type: "{self._escape_yaml_string(material.get("type", ""))}"')
                    yaml_lines.append(f'    title: "{self._escape_yaml_string(material.get("title", ""))}"')
                    yaml_lines.append(f'    url: "{self._escape_yaml_string(material.get("url", ""))}"')

            yaml_lines.append('---')

            # Prepare body content
            body = meeting.get('content', '')
            # Strip HTML tags for cleaner Markdown
            body = self._html_to_markdown(body)

            # Clean up excessive whitespace
            body = '\n'.join([line.rstrip() for line in body.split('\n')])

            # Combine frontmatter and body
            full_content = '\n'.join(yaml_lines) + '\n\n' + body

            # Write to file
            filename = f"{slug}.md"
            filepath = self.content_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)

            logger.info(f"Generated: {filepath}")
            return filename

        except Exception as e:
            logger.error(f"Error generating markdown for meeting '{meeting.get('title')}': {e}")
            return None

    def _html_to_markdown(self, html):
        """Simple HTML to Markdown conversion"""
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)

        # Remove HTML comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        # Convert basic HTML tags to markdown
        html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', html, flags=re.IGNORECASE)
        html = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', html, flags=re.IGNORECASE)
        html = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', html, flags=re.IGNORECASE)
        html = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', html, flags=re.IGNORECASE)
        html = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.IGNORECASE)

        # Remove remaining HTML tags
        html = re.sub(r'<[^>]+>', '', html)

        # Clean up whitespace
        html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)

        return html.strip()

    def organize_assets(self):
        """Organize and copy assets from WordPress migration folder"""
        logger.info("Organizing and copying assets...")

        migration_assets = self.project_root / 'AAII-Migration-assets' / 'uploads'

        if not migration_assets.exists():
            logger.warning(f"Migration assets folder not found: {migration_assets}")
            return

        # Copy all images from migration assets to public/images directories
        try:
            # Copy all images to meetings folder
            for year_folder in migration_assets.iterdir():
                if not year_folder.is_dir():
                    continue

                for month_folder in year_folder.iterdir():
                    if not month_folder.is_dir():
                        continue

                    for file in month_folder.iterdir():
                        if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                            try:
                                # Copy images to meetings folder
                                dest = self.images_meetings_dir / file.name
                                shutil.copy2(str(file), str(dest))
                                self.migration_report['assets_organized'].append(f"{file.name} (meeting image)")

                                # Check if it's a speaker image and copy to speakers folder too
                                if any(x in file.name.lower() for x in ['speaker', 'headshot', 'portrait', 'profile']):
                                    dest_speaker = self.images_speakers_dir / file.name
                                    if not dest_speaker.exists():
                                        shutil.copy2(str(file), str(dest_speaker))

                            except Exception as e:
                                logger.warning(f"Could not copy image {file.name}: {e}")
                                self.migration_report['missing_images'].append(str(file))

                        elif file.is_file() and file.suffix.lower() == '.pdf':
                            try:
                                # Copy PDFs to documents folder
                                dest = self.documents_dir / file.name
                                shutil.copy2(str(file), str(dest))
                                self.migration_report['assets_organized'].append(f"{file.name} (document)")

                            except Exception as e:
                                logger.warning(f"Could not copy PDF {file.name}: {e}")
                                self.migration_report['missing_pdfs'].append(str(file))

            logger.info(f"Asset organization complete: {len(self.migration_report['assets_organized'])} files copied")

        except Exception as e:
            logger.error(f"Error organizing assets: {e}")
            self.migration_report['errors'].append(f"Asset organization error: {str(e)}")

    def update_markdown_with_assets(self):
        """Update generated markdown files with correct asset paths"""
        logger.info("Updating markdown files with asset paths...")

        try:
            migration_assets = self.project_root / 'AAII-Migration-assets' / 'uploads'

            # Map image filenames to meetings
            for markdown_file in self.content_dir.glob('*.md'):
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Try to find relevant featured image from month folder
                # Extract date from markdown to match with assets folder
                date_match = re.search(r"date:\s*['\"](\d{4})-(\d{2})-(\d{2})", content)
                if date_match:
                    year = date_match.group(1)
                    month = date_match.group(2)

                    # Look for images in corresponding month folder
                    month_assets = migration_assets / year / month
                    if month_assets.exists():
                        # Find first non-speaker image as featured image
                        for image_file in month_assets.iterdir():
                            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                                if not any(x in image_file.name.lower() for x in ['speaker', 'headshot', '400x400', '150x150']):
                                    # Update the featured image path
                                    content = re.sub(
                                        r'image:\s*[\'"]([^\'"]+)[\'"]',
                                        f'image: "/images/meetings/{image_file.name}"',
                                        content
                                    )
                                    logger.info(f"Updated featured image in {markdown_file.name}")
                                    break

                # Update speaker image paths
                content = re.sub(
                    r'speakerImage:\s*[\'"]([^\'"]+)[\'"]',
                    lambda m: f'speakerImage: "/images/speakers/{Path(m.group(1)).name}"' if m.group(1) else 'speakerImage: ""',
                    content
                )

                # Update PDF paths
                content = re.sub(
                    r'url:\s*[\'"]([^\'"]*\.pdf)[\'"]',
                    lambda m: f'url: "/documents/meetings/{Path(m.group(1)).name}"' if m.group(1) else f'url: "{m.group(1)}"',
                    content
                )

                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(content)

        except Exception as e:
            logger.error(f"Error updating markdown files: {e}")
            self.migration_report['errors'].append(f"Markdown update error: {str(e)}")

    def generate_report(self):
        """Generate migration report"""
        report_path = self.project_root / 'migration-report.md'

        report_content = f"""# WordPress Meetings Migration Report

## Summary
- **Total Posts Processed:** {self.migration_report['total_posts_processed']}
- **Successful Migrations:** {self.migration_report['successful_migrations']}
- **Failed Migrations:** {self.migration_report['failed_migrations']}
- **Assets Organized:** {len(self.migration_report['assets_organized'])}
- **Migration Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## File Mapping
WordPress Post ID → Markdown Filename

"""

        for post_id, filename in self.migration_report['file_mapping'].items():
            report_content += f"- `{post_id}` → `{filename}`\n"

        if self.migration_report['assets_organized']:
            report_content += f"\n## Assets Organized ({len(self.migration_report['assets_organized'])} files)\n\n"
            for asset in sorted(self.migration_report['assets_organized'])[:50]:  # Show first 50
                report_content += f"- {asset}\n"
            if len(self.migration_report['assets_organized']) > 50:
                report_content += f"- ... and {len(self.migration_report['assets_organized']) - 50} more files\n"

        if self.migration_report['errors']:
            report_content += "\n## Errors Encountered\n\n"
            for error in self.migration_report['errors']:
                report_content += f"- {error}\n"

        if self.migration_report['missing_images']:
            report_content += "\n## Missing Images\n\n"
            for image in self.migration_report['missing_images'][:20]:
                report_content += f"- {image}\n"
            if len(self.migration_report['missing_images']) > 20:
                report_content += f"- ... and {len(self.migration_report['missing_images']) - 20} more\n"

        if self.migration_report['missing_pdfs']:
            report_content += "\n## Missing PDFs\n\n"
            for pdf in self.migration_report['missing_pdfs'][:20]:
                report_content += f"- {pdf}\n"
            if len(self.migration_report['missing_pdfs']) > 20:
                report_content += f"- ... and {len(self.migration_report['missing_pdfs']) - 20} more\n"

        report_content += f"\n## Directories Created\n\n"
        report_content += f"- `{self.content_dir}` - Markdown meeting files\n"
        report_content += f"- `{self.images_meetings_dir}` - Featured meeting images\n"
        report_content += f"- `{self.images_speakers_dir}` - Speaker headshots\n"
        report_content += f"- `{self.documents_dir}` - PDF materials and slides\n"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Migration report generated: {report_path}")

    def run(self):
        """Execute the complete migration process"""
        try:
            logger.info("=" * 60)
            logger.info("WordPress Meetings Migration Started")
            logger.info("=" * 60)

            self.setup_directories()
            self.parse_xml()
            self.process_meetings()
            self.organize_assets()
            self.update_markdown_with_assets()
            self.generate_report()

            logger.info("=" * 60)
            logger.info("WordPress Meetings Migration Completed Successfully")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False


def main():
    """Main entry point"""
    # Configuration
    PROJECT_ROOT = Path(__file__).parent.parent
    XML_FILE = PROJECT_ROOT / 'AAII-Migration-assets' / 'aaiilaorg.WordPress.2025-07-27 (1).xml'

    # Validate XML file exists
    if not XML_FILE.exists():
        logger.error(f"XML file not found: {XML_FILE}")
        return 1

    # Run migration
    extractor = MeetingExtractor(str(XML_FILE), PROJECT_ROOT)
    success = extractor.run()

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
