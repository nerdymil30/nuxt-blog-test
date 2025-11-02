#!/usr/bin/env python3
"""
High-Accuracy XML Data Extraction Script
Extracts structured data from WordPress/Visual Composer XML files with maximum fidelity
"""

import xml.etree.ElementTree as ET
import re
import json
import urllib.parse
import html as html_lib
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple
import csv
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / 'AAII-Migration-assets' / 'individual-posts'
OUTPUT_BASE = PROJECT_ROOT / 'AAII-Migration-assets' / 'output'
OUTPUT_XML = OUTPUT_BASE / 'structured-xml'
OUTPUT_JSON = OUTPUT_BASE / 'structured-json'

# Namespaces for XML parsing
NAMESPACES = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/'
}

# Data models
@dataclass
class Material:
    type: str  # 'recording', 'slides', 'document'
    url: str
    label: str
    status: str = 'not_validated'

@dataclass
class Speaker:
    name: str
    title: str
    bio: str = ''
    photo_id: str = ''

@dataclass
class Presentation:
    title: str
    description: str = ''
    learning_outcomes: List[str] = field(default_factory=list)

@dataclass
class Topic:
    id: int
    speaker: Speaker
    presentation: Presentation
    materials: List[Material] = field(default_factory=list)

@dataclass
class Meeting:
    # Basic metadata
    title: str
    link: str
    post_id: str
    post_name: str
    post_date: str
    category: str
    creator: str

    # Custom fields
    thumbnail_id: str = ''
    background_image: str = ''

    # Event info
    event_date: str = ''
    status: str = ''

    # Topics
    topics: List[Topic] = field(default_factory=list)

    # Metadata
    format_type: str = ''  # Format 1, 2, or 3
    processing_notes: List[str] = field(default_factory=list)

class ShortcodeParser:
    """Parse Visual Composer shortcodes"""

    @staticmethod
    def parse_attributes(shortcode_content: str) -> Dict[str, str]:
        """Extract attributes from shortcode"""
        attrs = {}
        # Pattern: attribute="value" or attribute='value'
        pattern = r'(\w+)=(["\'])((?:(?!\2).)*)\2'
        matches = re.finditer(pattern, shortcode_content)
        for match in matches:
            key, _, value = match.groups()
            attrs[key] = value
        return attrs

    @staticmethod
    def find_shortcode(tag: str, content: str) -> List[Tuple[str, Dict[str, str]]]:
        """Find all instances of a shortcode tag"""
        results = []
        # Pattern: [tag attributes]content[/tag] or [tag attributes]
        pattern = rf'\[{tag}([^\]]*)\](?:([^\[]*(?:\[[^\]]*\][^\[]*)*)\[/{tag}\])?'
        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            attrs_str, inner_content = match.groups()
            attrs = ShortcodeParser.parse_attributes(attrs_str)
            inner_content = inner_content or ''
            results.append((inner_content.strip(), attrs))
        return results

    @staticmethod
    def decode_url_param(param_string: str) -> Dict[str, str]:
        """Decode URL-encoded parameter like buttom_link_src"""
        result = {}
        if not param_string:
            return result

        # Split by pipe
        parts = param_string.split('|')
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                # URL decode the value
                decoded = urllib.parse.unquote(value)
                result[key] = decoded
        return result

    @staticmethod
    def extract_html_content(text: str) -> str:
        """Extract text from HTML tags and decode entities"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = html_lib.unescape(text)
        # Clean up whitespace
        text = ' '.join(text.split())
        return text

class DataExtractor:
    """Extract structured data from XML content"""

    def __init__(self):
        self.parser = ShortcodeParser()

    def detect_format(self, content: str) -> str:
        """Detect which format the content uses"""
        if 'TOPIC 1' in content or 'TOPIC 2' in content:
            return 'Format 1'
        elif re.search(r'\[dfd_heading[^\]]*subtitle=', content):
            return 'Format 2'
        elif 'PROGRAM' in content or 'Strategic Investing' in content:
            return 'Format 3'
        return 'Unknown'

    def extract_event_date(self, content: str) -> str:
        """Extract event date from content"""
        # Pattern: Saturday, May 17, 2025 or similar
        date_pattern = r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(\w+\s+\d{1,2},\s+\d{4})'
        match = re.search(date_pattern, content)
        if match:
            return match.group(0)
        return ''

    def extract_learning_outcomes(self, list_fields: str) -> List[str]:
        """Extract learning outcomes from JSON-encoded list_fields"""
        outcomes = []
        try:
            # URL decode first
            decoded = urllib.parse.unquote(list_fields)
            # Parse as JSON
            data = json.loads(decoded)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'text_content' in item:
                        outcome = self.parser.extract_html_content(item['text_content'])
                        if outcome:
                            outcomes.append(outcome)
        except (json.JSONDecodeError, ValueError) as e:
            pass  # Graceful degradation
        return outcomes

    def extract_speaker_from_team_member(self, attrs: Dict[str, str]) -> Speaker:
        """Extract speaker info from dfd_new_team_member shortcode"""
        name = attrs.get('team_member_name', '')
        title = attrs.get('team_member_job_position', '')
        photo_id = attrs.get('team_member_photo', '')
        # Bio is usually in separate vc_column_text, will be added later
        return Speaker(name=name, title=title, photo_id=photo_id)

    def extract_materials(self, content: str, topic_section: str) -> List[Material]:
        """Extract recording/slides links from topic section"""
        materials = []

        # Find dfd_button shortcodes
        buttons = self.parser.find_shortcode('dfd_button', topic_section)
        for button_content, button_attrs in buttons:
            button_text = button_attrs.get('button_text', '')
            link_src = button_attrs.get('buttom_link_src', '')

            # Parse the link source
            link_params = self.parser.decode_url_param(link_src)
            url = link_params.get('url', '')
            label = link_params.get('title', button_text)

            # Determine material type
            mat_type = 'recording'
            if 'slide' in button_text.lower() or 'pdf' in url.lower():
                mat_type = 'slides'
            elif 'document' in button_text.lower():
                mat_type = 'document'

            if url:
                materials.append(Material(
                    type=mat_type,
                    url=url,
                    label=label
                ))

        return materials

    def extract_topic_format1(self, content: str, topic_num: int, topic_section: str) -> Optional[Topic]:
        """Extract topic from Format 1 (TOPIC 1/TOPIC 2)"""
        # Extract speaker from team_member
        team_members = self.parser.find_shortcode('dfd_new_team_member', topic_section)
        if not team_members:
            return None

        _, tm_attrs = team_members[0]
        speaker = self.extract_speaker_from_team_member(tm_attrs)

        # Extract presentation title (from dfd_heading with tag:h2)
        headings = self.parser.find_shortcode('dfd_heading', topic_section)
        pres_title = ''
        for heading_content, heading_attrs in headings:
            title_opts = heading_attrs.get('title_font_options', '')
            if 'tag:h2' in title_opts:
                pres_title = self.parser.extract_html_content(heading_content)
                break

        # Extract description and bio from vc_column_text
        texts = self.parser.find_shortcode('vc_column_text', topic_section)
        description = ''
        bio = ''

        for text_content, _ in texts:
            clean_text = self.parser.extract_html_content(text_content)
            # Bio usually mentions the speaker name
            if speaker.name and speaker.name in clean_text:
                bio = clean_text
            elif clean_text and not description:
                description = clean_text

        if bio:
            speaker.bio = bio

        # Extract learning outcomes
        outcomes = []
        icon_lists = self.parser.find_shortcode('dfd_icon_list', topic_section)
        for _, il_attrs in icon_lists:
            list_fields = il_attrs.get('list_fields', '')
            if list_fields:
                outcomes = self.extract_learning_outcomes(list_fields)
                break

        # Extract materials
        materials = self.extract_materials(content, topic_section)

        presentation = Presentation(
            title=pres_title,
            description=description,
            learning_outcomes=outcomes
        )

        return Topic(
            id=topic_num,
            speaker=speaker,
            presentation=presentation,
            materials=materials
        )

    def extract_topics_format1(self, content: str) -> List[Topic]:
        """Extract all topics from Format 1"""
        topics = []

        # Split by TOPIC markers
        topic_pattern = r'TOPIC (\d+)'
        splits = re.split(topic_pattern, content)

        # Process pairs of (topic_num, topic_content)
        for i in range(1, len(splits), 2):
            if i + 1 < len(splits):
                topic_num = int(splits[i])
                topic_section = splits[i + 1]

                topic = self.extract_topic_format1(content, topic_num, topic_section)
                if topic:
                    topics.append(topic)

        return topics

    def extract_topics_format2(self, content: str) -> List[Topic]:
        """Extract topics from Format 2 (TOPICS with subtitle)"""
        topics = []
        topic_id = 1

        # Find headings with subtitle attribute
        headings = self.parser.find_shortcode('dfd_heading', content)
        for heading_content, heading_attrs in headings:
            subtitle = heading_attrs.get('subtitle', '')
            if subtitle:  # Speaker name in subtitle
                speaker = Speaker(name=subtitle, title='')
                pres_title = self.parser.extract_html_content(heading_content)

                # Find description in nearby vc_column_text
                # This is a simplified approach - may need refinement
                texts = self.parser.find_shortcode('vc_column_text', content)
                description = ''
                for text_content, _ in texts:
                    clean_text = self.parser.extract_html_content(text_content)
                    if clean_text and len(clean_text) > 50:
                        description = clean_text
                        break

                presentation = Presentation(title=pres_title, description=description)

                topics.append(Topic(
                    id=topic_id,
                    speaker=speaker,
                    presentation=presentation
                ))
                topic_id += 1

        return topics

    def extract_topics_format3(self, content: str) -> List[Topic]:
        """Extract topic from Format 3 (PROGRAM/single presenter)"""
        topics = []

        # Find team member
        team_members = self.parser.find_shortcode('dfd_new_team_member', content)
        if not team_members:
            return topics

        _, tm_attrs = team_members[0]
        speaker = self.extract_speaker_from_team_member(tm_attrs)

        # Find presentation title
        headings = self.parser.find_shortcode('dfd_heading', content)
        pres_title = ''
        for heading_content, heading_attrs in headings:
            clean_heading = self.parser.extract_html_content(heading_content)
            if clean_heading and len(clean_heading) > 10 and 'PROGRAM' not in clean_heading:
                pres_title = clean_heading
                break

        # Extract description
        texts = self.parser.find_shortcode('vc_column_text', content)
        description = ''
        bio = ''
        for text_content, _ in texts:
            clean_text = self.parser.extract_html_content(text_content)
            if speaker.name and speaker.name in clean_text:
                bio = clean_text
            elif clean_text and len(clean_text) > 30:
                description = clean_text

        if bio:
            speaker.bio = bio

        # Extract materials
        materials = self.extract_materials(content, content)

        presentation = Presentation(title=pres_title, description=description)

        topics.append(Topic(
            id=1,
            speaker=speaker,
            presentation=presentation,
            materials=materials
        ))

        return topics

class XMLProcessor:
    """Process XML files and extract structured data"""

    def __init__(self):
        self.extractor = DataExtractor()
        self.stats = {
            'processed': 0,
            'success': 0,
            'partial': 0,
            'failed': 0,
            'formats': {'Format 1': 0, 'Format 2': 0, 'Format 3': 0, 'Unknown': 0}
        }

    def process_file(self, xml_file: Path) -> Optional[Meeting]:
        """Process a single XML file"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Extract basic metadata
            title = root.findtext('title', '').strip()
            link = root.findtext('link', '').strip()
            post_id = root.findtext('wp:post_id', '', NAMESPACES).strip()
            post_name = root.findtext('wp:post_name', '', NAMESPACES).strip()
            post_date = root.findtext('wp:post_date', '', NAMESPACES).strip()
            creator = root.findtext('dc:creator', '', NAMESPACES).strip()

            # Extract category
            category_elem = root.find('category')
            category = category_elem.text if category_elem is not None else ''

            # Extract custom fields
            thumbnail_id = ''
            background_image = ''

            for postmeta in root.findall('wp:postmeta', NAMESPACES):
                meta_key = postmeta.findtext('wp:meta_key', '', NAMESPACES)
                meta_value = postmeta.findtext('wp:meta_value', '', NAMESPACES)

                if meta_key == '_thumbnail_id':
                    thumbnail_id = meta_value
                elif meta_key == 'stunnig_headers_bg_img':
                    background_image = meta_value

            # Extract content
            content_elem = root.find('content:encoded', NAMESPACES)
            content = content_elem.text if content_elem is not None else ''

            if not content:
                return None

            # Detect format
            format_type = self.extractor.detect_format(content)
            self.stats['formats'][format_type] = self.stats['formats'].get(format_type, 0) + 1

            # Extract event date and status
            event_date = self.extractor.extract_event_date(content)
            status = 'ARCHIVED' if 'ARCHIVE' in title.upper() else ''

            # Extract topics based on format
            topics = []
            if format_type == 'Format 1':
                topics = self.extractor.extract_topics_format1(content)
            elif format_type == 'Format 2':
                topics = self.extractor.extract_topics_format2(content)
            elif format_type == 'Format 3':
                topics = self.extractor.extract_topics_format3(content)

            # Create meeting object
            meeting = Meeting(
                title=title,
                link=link,
                post_id=post_id,
                post_name=post_name,
                post_date=post_date,
                category=category,
                creator=creator,
                thumbnail_id=thumbnail_id,
                background_image=background_image,
                event_date=event_date,
                status=status,
                topics=topics,
                format_type=format_type
            )

            # Update stats
            if topics:
                self.stats['success'] += 1
            else:
                self.stats['partial'] += 1
                meeting.processing_notes.append('No topics extracted')

            self.stats['processed'] += 1
            return meeting

        except Exception as e:
            self.stats['failed'] += 1
            self.stats['processed'] += 1
            print(f"ERROR processing {xml_file.name}: {e}")
            return None

    def process_all(self) -> List[Meeting]:
        """Process all XML files in input directory"""
        meetings = []
        xml_files = sorted(INPUT_DIR.glob('*.xml'))

        print(f"Processing {len(xml_files)} XML files...")
        print("=" * 80)

        for i, xml_file in enumerate(xml_files, 1):
            print(f"{i}. Processing {xml_file.name}...")
            meeting = self.process_file(xml_file)
            if meeting:
                meetings.append(meeting)

        print("\n" + "=" * 80)
        print("Processing complete!")
        print(f"Processed: {self.stats['processed']}")
        print(f"Success: {self.stats['success']}")
        print(f"Partial: {self.stats['partial']}")
        print(f"Failed: {self.stats['failed']}")

        return meetings

class OutputGenerator:
    """Generate various output formats"""

    @staticmethod
    def generate_xml(meeting: Meeting, output_path: Path):
        """Generate clean structured XML"""
        root = ET.Element('meeting')

        # Metadata
        metadata = ET.SubElement(root, 'metadata')
        ET.SubElement(metadata, 'title').text = meeting.title
        ET.SubElement(metadata, 'link').text = meeting.link
        ET.SubElement(metadata, 'post_id').text = meeting.post_id
        ET.SubElement(metadata, 'post_name').text = meeting.post_name
        ET.SubElement(metadata, 'post_date').text = meeting.post_date
        ET.SubElement(metadata, 'category').text = meeting.category
        ET.SubElement(metadata, 'creator').text = meeting.creator

        # Custom fields
        if meeting.thumbnail_id or meeting.background_image:
            custom_fields = ET.SubElement(root, 'custom_fields')
            if meeting.background_image:
                field = ET.SubElement(custom_fields, 'field')
                ET.SubElement(field, 'meta_key').text = 'stunnig_headers_bg_img'
                ET.SubElement(field, 'meta_value').text = meeting.background_image
            if meeting.thumbnail_id:
                field = ET.SubElement(custom_fields, 'field')
                ET.SubElement(field, 'meta_key').text = '_thumbnail_id'
                ET.SubElement(field, 'meta_value').text = meeting.thumbnail_id

        # Event
        if meeting.event_date or meeting.status:
            event = ET.SubElement(root, 'event')
            if meeting.event_date:
                ET.SubElement(event, 'date').text = meeting.event_date
            if meeting.status:
                ET.SubElement(event, 'status').text = meeting.status

        # Topics
        topics_elem = ET.SubElement(root, 'topics')
        for topic in meeting.topics:
            topic_elem = ET.SubElement(topics_elem, 'topic', id=str(topic.id))

            # Speaker
            speaker_elem = ET.SubElement(topic_elem, 'speaker')
            ET.SubElement(speaker_elem, 'name').text = topic.speaker.name
            ET.SubElement(speaker_elem, 'title').text = topic.speaker.title
            if topic.speaker.photo_id:
                ET.SubElement(speaker_elem, 'photo_id').text = topic.speaker.photo_id
            if topic.speaker.bio:
                ET.SubElement(speaker_elem, 'bio').text = topic.speaker.bio

            # Presentation
            pres_elem = ET.SubElement(topic_elem, 'presentation')
            ET.SubElement(pres_elem, 'title').text = topic.presentation.title
            if topic.presentation.description:
                ET.SubElement(pres_elem, 'description').text = topic.presentation.description

            if topic.presentation.learning_outcomes:
                outcomes_elem = ET.SubElement(pres_elem, 'learning_outcomes')
                for outcome in topic.presentation.learning_outcomes:
                    ET.SubElement(outcomes_elem, 'outcome').text = outcome

            # Materials
            if topic.materials:
                materials_elem = ET.SubElement(topic_elem, 'materials')
                for material in topic.materials:
                    mat_elem = ET.SubElement(materials_elem, material.type)
                    ET.SubElement(mat_elem, 'url').text = material.url
                    ET.SubElement(mat_elem, 'label').text = material.label
                    ET.SubElement(mat_elem, 'status').text = material.status

        # Write to file
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(output_path, encoding='utf-8', xml_declaration=True)

    @staticmethod
    def meeting_to_dict(meeting: Meeting) -> dict:
        """Convert meeting to dictionary for JSON"""
        return {
            'metadata': {
                'title': meeting.title,
                'link': meeting.link,
                'post_id': meeting.post_id,
                'post_name': meeting.post_name,
                'post_date': meeting.post_date,
                'category': meeting.category,
                'creator': meeting.creator
            },
            'custom_fields': {
                'thumbnail_id': meeting.thumbnail_id,
                'background_image': meeting.background_image
            },
            'event': {
                'date': meeting.event_date,
                'status': meeting.status
            },
            'topics': [
                {
                    'id': t.id,
                    'speaker': {
                        'name': t.speaker.name,
                        'title': t.speaker.title,
                        'bio': t.speaker.bio,
                        'photo_id': t.speaker.photo_id
                    },
                    'presentation': {
                        'title': t.presentation.title,
                        'description': t.presentation.description,
                        'learning_outcomes': t.presentation.learning_outcomes
                    },
                    'materials': [
                        {
                            'type': m.type,
                            'url': m.url,
                            'label': m.label,
                            'status': m.status
                        } for m in t.materials
                    ]
                } for t in meeting.topics
            ],
            'format_type': meeting.format_type,
            'processing_notes': meeting.processing_notes
        }

    @staticmethod
    def generate_json(meeting: Meeting, output_path: Path):
        """Generate JSON output"""
        data = OutputGenerator.meeting_to_dict(meeting)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def generate_consolidated_json(meetings: List[Meeting], output_path: Path):
        """Generate consolidated JSON with all meetings"""
        data = {
            'total_meetings': len(meetings),
            'generated_at': datetime.now().isoformat(),
            'meetings': [OutputGenerator.meeting_to_dict(m) for m in meetings]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def generate_csv(meetings: List[Meeting], output_path: Path):
        """Generate CSV export (denormalized)"""
        rows = []
        for meeting in meetings:
            for topic in meeting.topics:
                row = {
                    'post_id': meeting.post_id,
                    'title': meeting.title,
                    'post_date': meeting.post_date,
                    'event_date': meeting.event_date,
                    'category': meeting.category,
                    'link': meeting.link,
                    'topic_id': topic.id,
                    'speaker_name': topic.speaker.name,
                    'speaker_title': topic.speaker.title,
                    'presentation_title': topic.presentation.title,
                    'learning_outcomes_count': len(topic.presentation.learning_outcomes),
                    'materials_count': len(topic.materials),
                    'format_type': meeting.format_type
                }
                rows.append(row)

        if rows:
            fieldnames = rows[0].keys()
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

def main():
    """Main execution"""
    print("=" * 80)
    print("HIGH-ACCURACY XML DATA EXTRACTION")
    print("=" * 80)
    print()

    # Create output directories
    OUTPUT_BASE.mkdir(exist_ok=True)
    OUTPUT_XML.mkdir(exist_ok=True)
    OUTPUT_JSON.mkdir(exist_ok=True)

    # Process all files
    processor = XMLProcessor()
    meetings = processor.process_all()

    print(f"\nGenerating outputs for {len(meetings)} meetings...")

    # Generate individual outputs
    for meeting in meetings:
        # XML
        xml_path = OUTPUT_XML / f"{meeting.post_name}.xml"
        OutputGenerator.generate_xml(meeting, xml_path)

        # JSON
        json_path = OUTPUT_JSON / f"{meeting.post_name}.json"
        OutputGenerator.generate_json(meeting, json_path)

    # Generate consolidated outputs
    consolidated_json = OUTPUT_BASE / 'all-meetings-consolidated.json'
    OutputGenerator.generate_consolidated_json(meetings, consolidated_json)

    csv_output = OUTPUT_BASE / 'meetings-export.csv'
    OutputGenerator.generate_csv(meetings, csv_output)

    print("\n" + "=" * 80)
    print("OUTPUT GENERATED")
    print("=" * 80)
    print(f"Structured XML: {OUTPUT_XML} ({len(list(OUTPUT_XML.glob('*.xml')))} files)")
    print(f"Structured JSON: {OUTPUT_JSON} ({len(list(OUTPUT_JSON.glob('*.json')))} files)")
    print(f"Consolidated JSON: {consolidated_json}")
    print(f"CSV Export: {csv_output}")

    # Print stats
    print("\n" + "=" * 80)
    print("PROCESSING STATISTICS")
    print("=" * 80)
    print(f"Files processed: {processor.stats['processed']}/50")
    print(f"Full extraction success: {processor.stats['success']}/50")
    print(f"Partial extraction: {processor.stats['partial']}/50")
    print(f"Failed: {processor.stats['failed']}/50")
    print(f"\nFormat distribution:")
    for fmt, count in processor.stats['formats'].items():
        print(f"  {fmt}: {count}")

    # Calculate data completeness
    total_topics = sum(len(m.topics) for m in meetings)
    topics_with_speaker = sum(1 for m in meetings for t in m.topics if t.speaker.name)
    topics_with_title = sum(1 for m in meetings for t in m.topics if t.presentation.title)
    topics_with_outcomes = sum(1 for m in meetings for t in m.topics if t.presentation.learning_outcomes)
    topics_with_materials = sum(1 for m in meetings for t in m.topics if t.materials)

    print(f"\nData completeness (across {total_topics} topics):")
    print(f"  Speaker names: {topics_with_speaker}/{total_topics} ({topics_with_speaker/total_topics*100:.1f}%)")
    print(f"  Presentation titles: {topics_with_title}/{total_topics} ({topics_with_title/total_topics*100:.1f}%)")
    print(f"  Learning outcomes: {topics_with_outcomes}/{total_topics} ({topics_with_outcomes/total_topics*100:.1f}%)")
    print(f"  Materials/links: {topics_with_materials}/{total_topics} ({topics_with_materials/total_topics*100:.1f}%)")

    print("\n✓ Extraction complete!")

if __name__ == '__main__':
    main()
