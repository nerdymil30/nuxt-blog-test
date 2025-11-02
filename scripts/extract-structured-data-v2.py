#!/usr/bin/env python3
"""
Enhanced XML Data Extraction Script - Version 2
Improvements:
- Detects ALL TOPIC markers (not just those with team_member)
- Implements fuzzy matching for materials to topics
- Handles joint presentations
"""

import xml.etree.ElementTree as ET
import re
import json
import urllib.parse
import html
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import sys

PROJECT_ROOT = Path(__file__).parent.parent
INDIVIDUAL_POSTS = PROJECT_ROOT / 'AAII-Migration-assets' / 'individual-posts' / 'monthly-meetings'
OUTPUT_XML = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-xml'
OUTPUT_JSON = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-json'


@dataclass
class Material:
    type: str
    url: str
    label: str


@dataclass
class Speaker:
    name: str
    title: str
    bio: str
    photo_id: str


@dataclass
class Presentation:
    title: str
    description: str
    learning_outcomes: List[str]


@dataclass
class Topic:
    id: int
    speakers: List[Speaker]  # Changed from singular to plural to support multiple speakers
    presentation: Presentation
    materials: List[Material]


@dataclass
class Meeting:
    metadata: Dict[str, str]
    custom_fields: List[Dict[str, str]]
    event_date: str
    topics: List[Topic]


class ShortcodeParser:
    """Parses WordPress Visual Composer shortcodes"""

    @staticmethod
    def parse_attributes(shortcode_content: str) -> Dict[str, str]:
        """Extract attributes from shortcode"""
        attrs = {}
        # Match key="value" or key=value patterns
        pattern = r'(\w+)=(?:"([^"]*)"|([^\s\]]+))'
        matches = re.finditer(pattern, shortcode_content)
        for match in matches:
            key = match.group(1)
            value = match.group(2) if match.group(2) is not None else match.group(3)
            attrs[key] = value
        return attrs

    @staticmethod
    def find_shortcode(tag: str, content: str) -> List[Tuple[str, Dict[str, str]]]:
        """Find all instances of a shortcode tag and return (full_content, attributes)"""
        pattern = rf'\[{tag}([^\]]*)\](.*?)\[/{tag}\]'
        results = []
        for match in re.finditer(pattern, content, re.DOTALL):
            attrs = ShortcodeParser.parse_attributes(match.group(1))
            inner_content = match.group(2)
            results.append((inner_content, attrs))
        return results

    @staticmethod
    def decode_url_param(param_string: str) -> Dict[str, str]:
        """Decode URL-encoded parameter string like 'url:...| title:...|target:...'"""
        decoded = urllib.parse.unquote(param_string)
        parts = {}
        for part in decoded.split('|'):
            if ':' in part:
                key, value = part.split(':', 1)
                parts[key.strip()] = value.strip()
        return parts

    @staticmethod
    def extract_html_content(text: str) -> str:
        """Extract text from HTML tags and decode entities"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = html.unescape(text)
        # Clean up whitespace
        text = ' '.join(text.split())
        return text


class DataExtractor:
    """Extracts structured data from WordPress XML"""

    def __init__(self):
        self.parser = ShortcodeParser()

    def detect_format(self, content: str) -> str:
        """Detect which format the content uses"""
        if re.search(r'\[dfd_heading[^\]]*\]TOPIC \d+\[/dfd_heading\]', content):
            return "Format 1: TOPIC 1/2/3"
        elif 'TOPICS' in content and 'subtitle=' in content:
            return "Format 2: TOPICS with subtitle"
        else:
            return "Format 3: PROGRAM/Single"

    def extract_event_date(self, content: str) -> str:
        """Extract event date from content"""
        # Look for date patterns like "Saturday, April 17, 2021"
        date_pattern = r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+([A-Za-z]+\s+\d+,\s+\d{4})'
        match = re.search(date_pattern, content)
        return match.group(0) if match else "Unknown"

    def extract_learning_outcomes(self, list_fields: str) -> List[str]:
        """Extract learning outcomes from JSON-encoded list_fields"""
        try:
            decoded = urllib.parse.unquote(list_fields)
            data = json.loads(decoded)
            outcomes = []
            for item in data:
                if 'text_content' in item:
                    text = item['text_content'].replace('\\n', '').strip()
                    outcomes.append(text)
            return outcomes
        except:
            return []

    def extract_speaker_from_team_member(self, attrs: Dict[str, str]) -> Speaker:
        """Extract speaker info from dfd_new_team_member shortcode"""
        return Speaker(
            name=attrs.get('team_member_name', ''),
            title=attrs.get('team_member_job_position', ''),
            bio=attrs.get('team_member_description', ''),
            photo_id=attrs.get('team_member_photo', '')
        )

    def extract_all_topic_markers(self, content: str) -> List[Tuple[int, str]]:
        """
        Extract ALL TOPIC markers and their content sections.
        Returns list of (topic_number, section_content) tuples
        """
        # Find all TOPIC headings
        topic_pattern = r'\[dfd_heading[^\]]*\]TOPIC (\d+)\[/dfd_heading\]'
        topic_matches = list(re.finditer(topic_pattern, content))

        if not topic_matches:
            return []

        topics = []
        for i, match in enumerate(topic_matches):
            topic_num = int(match.group(1))
            start_pos = match.end()

            # Find end position (start of next TOPIC or end of content)
            if i + 1 < len(topic_matches):
                end_pos = topic_matches[i + 1].start()
            else:
                # Look for materials section or end of content
                materials_match = re.search(r'WEBINAR ARCHIVE MATERIALS', content[start_pos:])
                if materials_match:
                    end_pos = start_pos + materials_match.start()
                else:
                    end_pos = len(content)

            section_content = content[start_pos:end_pos]
            topics.append((topic_num, section_content))

        return topics

    def extract_materials_from_section(self, section_content: str) -> List[Material]:
        """Extract materials (buttons with links) from a specific section"""
        materials = []

        # Find all button links in this section
        button_pattern = r'\[dfd_button[^\]]*button_text="([^"]+)"[^\]]*buttom_link_src="([^"]+)"'
        button_matches = re.finditer(button_pattern, section_content)

        for match in button_matches:
            button_text = match.group(1)
            link_params = match.group(2)

            # Skip donation links
            if 'donation' in button_text.lower():
                continue

            # Decode URL parameters
            url_parts = self.parser.decode_url_param(link_params)
            url = url_parts.get('url', '')

            if not url:
                continue

            # Determine material type
            material_type = 'recording'
            if 'slides' in button_text.lower() or url.endswith('.pdf'):
                material_type = 'slides'
            elif 'youtube' in url or 'youtu.be' in url:
                material_type = 'recording'

            materials.append(Material(
                type=material_type,
                url=url,
                label=button_text
            ))

        return materials

    def extract_topic_content(self, topic_section: str) -> Tuple[List[Speaker], Presentation, List[Material]]:
        """
        Extract speakers, presentation info, and materials from a topic section.
        Handles sections with or without dfd_new_team_member.
        Supports multiple speakers per topic (e.g., panel sessions).
        Returns: (speakers_list, presentation, materials)
        """
        speakers = []

        # Extract ALL speakers from team_member shortcodes (not just the first one)
        team_member_pattern = r'\[dfd_new_team_member([^\]]+)\]'
        team_matches = re.finditer(team_member_pattern, topic_section)

        for team_match in team_matches:
            attrs = self.parser.parse_attributes(team_match.group(1))
            speaker = self.extract_speaker_from_team_member(attrs)
            if speaker:
                speakers.append(speaker)

        # Extract presentation title
        title = ""
        # Try dfd_heading with content
        heading_pattern = r'\[dfd_heading[^\]]*\](.*?)\[/dfd_heading\]'
        heading_matches = re.finditer(heading_pattern, topic_section)
        for match in heading_matches:
            content = match.group(1)
            # Skip if it's just "TOPIC X"
            if 'TOPIC' not in content:
                extracted = self.parser.extract_html_content(content)
                if extracted and len(extracted) > 10:
                    title = extracted
                    break

        # If not found, try h2/h4 tags
        if not title:
            h_pattern = r'<(?:h2|h4)[^>]*>(.*?)</(?:h2|h4)>'
            h_match = re.search(h_pattern, topic_section)
            if h_match:
                title = self.parser.extract_html_content(h_match.group(1))

        # Extract description
        description = ""
        desc_pattern = r'\[vc_column_text\](.*?)\[/vc_column_text\]'
        desc_matches = re.finditer(desc_pattern, topic_section, re.DOTALL)
        for match in desc_matches:
            content = match.group(1)
            # Skip "You will learn..." sections
            if 'You will learn' not in content and 'ARCHIVE MATERIALS' not in content:
                extracted = self.parser.extract_html_content(content)
                if extracted and len(extracted) > 20:
                    description = extracted
                    break

        # Extract learning outcomes
        learning_outcomes = []
        list_pattern = r'\[dfd_icon_list[^\]]*list_fields="([^"]+)"'
        list_match = re.search(list_pattern, topic_section)
        if list_match:
            learning_outcomes = self.extract_learning_outcomes(list_match.group(1))

        # Extract bios for ALL speakers - bios come AFTER learning outcomes in vc_column_text
        if speakers:
            # Find the position of learning outcomes
            list_pos = list_match.end() if list_match else 0

            # Look for vc_column_text sections after learning outcomes
            desc_matches = re.finditer(desc_pattern, topic_section[list_pos:], re.DOTALL)
            bio_candidates = []

            for match in desc_matches:
                content = match.group(1)
                extracted = self.parser.extract_html_content(content)

                # Bio typically is substantial (>50 chars) and contains bio-like keywords
                if extracted and len(extracted) > 50:
                    if any(keyword in extracted.lower() for keyword in ['founded', 'formerly', 'worked', 'holds', 'phd', 'mba', 'experience', 'graduated', 'retired', 'educated']):
                        bio_candidates.append(extracted)

            # Try to match bios to speakers by name
            for speaker in speakers:
                if speaker.name:
                    # Find bio that contains this speaker's first or last name
                    name_parts = speaker.name.split()
                    for bio_text in bio_candidates:
                        if any(name_part in bio_text for name_part in name_parts if len(name_part) > 3):
                            speaker.bio = bio_text
                            bio_candidates.remove(bio_text)
                            break

            # If there are remaining bios and speakers without bios, assign in order
            speakers_without_bio = [s for s in speakers if not s.bio]
            for i, speaker in enumerate(speakers_without_bio):
                if i < len(bio_candidates):
                    speaker.bio = bio_candidates[i]

        presentation = Presentation(
            title=title,
            description=description,
            learning_outcomes=learning_outcomes
        )

        # Extract materials from this topic section
        materials = self.extract_materials_from_section(topic_section)

        return speakers, presentation, materials

    def extract_materials_with_fuzzy_matching(self, content: str, topics: List[Topic]) -> None:
        """
        Extract materials and associate them with topics using fuzzy matching.
        Only processes materials not already found in topic sections.
        Modifies topics in-place to add materials.
        """
        # Get URLs of materials already extracted from topic sections
        already_extracted_urls = set()
        for topic in topics:
            for material in topic.materials:
                already_extracted_urls.add(material.url.rstrip('/'))

        # Extract all button links
        button_pattern = r'\[dfd_button[^\]]*button_text="([^"]+)"[^\]]*buttom_link_src="([^"]+)"'
        button_matches = re.finditer(button_pattern, content)

        all_materials = []
        for match in button_matches:
            button_text = match.group(1)
            link_params = match.group(2)

            # Skip donation links
            if 'donation' in button_text.lower():
                continue

            # Decode URL parameters
            url_parts = self.parser.decode_url_param(link_params)
            url = url_parts.get('url', '')

            if not url:
                continue

            # Skip if this URL was already extracted from a topic section
            if url.rstrip('/') in already_extracted_urls:
                continue

            # Determine material type
            material_type = 'recording'
            if 'slides' in button_text.lower() or url.endswith('.pdf'):
                material_type = 'slides'
            elif 'youtube' in url or 'youtu.be' in url:
                material_type = 'recording'

            material = Material(
                type=material_type,
                url=url,
                label=button_text
            )
            all_materials.append((button_text, material))

        # Fuzzy match materials to topics
        for button_text, material in all_materials:
            matched_topic = None
            button_lower = button_text.lower()

            # Strategy 1: Match by part numbers FIRST (most reliable)
            part_match = re.search(r'part\s*(\d+)', button_lower)
            if part_match:
                part_num = int(part_match.group(1))
                if 1 <= part_num <= len(topics):
                    matched_topic = topics[part_num - 1]

            # Strategy 2: Special handling for "duo" or "joint" presentations
            if not matched_topic:
                if 'duo' in button_lower or 'joint' in button_lower:
                    # Assign to last topic (likely the joint presentation)
                    matched_topic = topics[-1] if topics else None

            # Strategy 3: Match by full speaker name (exact match preferred)
            if not matched_topic:
                for topic in topics:
                    for speaker in topic.speakers:
                        if speaker and speaker.name:
                            full_name = speaker.name.lower()
                            # Check for exact full name match
                            if full_name in button_lower:
                                matched_topic = topic
                                break
                    if matched_topic:
                        break

            # Strategy 4: Match by unique parts of speaker name
            if not matched_topic:
                for topic in topics:
                    for speaker in topic.speakers:
                        if speaker and speaker.name:
                            # For names like "Gatis Roze" vs "Grayson Roze", use first name
                            name_parts = speaker.name.split()
                            if len(name_parts) >= 2:
                                first_name = name_parts[0].lower()
                                # Match first name if it's unique and substantial
                                if len(first_name) > 4 and first_name in button_lower:
                                    matched_topic = topic
                                    break
                    if matched_topic:
                        break

            # Strategy 5: Position-based fallback
            if not matched_topic and len(all_materials) == len(topics) * 2:
                # If we have exactly 2 materials per topic, assign sequentially
                material_index = all_materials.index((button_text, material))
                topic_index = material_index // 2
                if topic_index < len(topics):
                    matched_topic = topics[topic_index]

            # Add material to matched topic
            if matched_topic:
                matched_topic.materials.append(material)

    def extract_topics_enhanced(self, content: str) -> List[Topic]:
        """
        Enhanced topic extraction that finds ALL topics, not just those with team_member.
        Includes fallback for single-speaker files without TOPIC markers.
        Handles speaker appearing before TOPIC 1 marker (same speaker for all topics).
        """
        # Get all topic markers and their content
        topic_sections = self.extract_all_topic_markers(content)

        # Check for speaker info BEFORE first TOPIC marker (same speaker for multiple topics)
        pre_topic_speaker = None
        if topic_sections:
            # Find position of first TOPIC marker
            first_topic_pattern = r'\[dfd_heading[^\]]*\]TOPIC 1\[/dfd_heading\]'
            first_topic_match = re.search(first_topic_pattern, content)

            if first_topic_match:
                pre_topic_content = content[:first_topic_match.start()]

                # Check if there's a team_member in the pre-topic content
                team_member_pattern = r'\[dfd_new_team_member([^\]]+)\]'
                team_match = re.search(team_member_pattern, pre_topic_content)

                if team_match:
                    attrs = self.parser.parse_attributes(team_match.group(1))
                    pre_topic_speaker = self.extract_speaker_from_team_member(attrs)

                    # Extract bio from pre-topic content if available
                    if pre_topic_speaker and pre_topic_speaker.name:
                        desc_pattern = r'\[vc_column_text\](.*?)\[/vc_column_text\]'
                        desc_matches = re.finditer(desc_pattern, pre_topic_content, re.DOTALL)

                        for match in desc_matches:
                            bio_content = match.group(1)
                            extracted = self.parser.extract_html_content(bio_content)

                            # Bio should contain speaker's name and be substantial
                            if extracted and len(extracted) > 100:
                                name_parts = pre_topic_speaker.name.split()
                                if any(name_part in extracted for name_part in name_parts if len(name_part) > 3):
                                    pre_topic_speaker.bio = extracted
                                    break

        # Fallback: If no TOPIC markers found, check for single-speaker format
        if not topic_sections:
            # Check if this is a single-speaker file (has dfd_new_team_member)
            team_member_pattern = r'\[dfd_new_team_member'
            if re.search(team_member_pattern, content):
                # Treat entire content as implicit TOPIC 1
                print("  ⚠ No TOPIC markers found - using single-speaker fallback mode")
                speakers, presentation, materials = self.extract_topic_content(content)

                # Create single topic
                topic = Topic(
                    id=1,
                    speakers=speakers,
                    presentation=presentation,
                    materials=materials
                )
                return [topic]
            else:
                # No topics and no speaker - truly empty
                return []

        topics = []
        for topic_num, section_content in topic_sections:
            # Extract speakers, presentation, and materials from this section
            speakers, presentation, materials = self.extract_topic_content(section_content)

            # Special handling: If pre-topic speaker exists and this is Topic 1, use pre-topic speaker
            # For Topic 2+, leave speakers empty (same speaker for all topics case)
            if pre_topic_speaker and topic_num == 1:
                speakers = [pre_topic_speaker]
            elif pre_topic_speaker and topic_num > 1:
                # Same speaker for multiple topics - only assign to Topic 1
                speakers = []

            # Create topic with materials from section
            topic = Topic(
                id=topic_num,
                speakers=speakers,
                presentation=presentation,
                materials=materials
            )
            topics.append(topic)

        # Also do fuzzy matching for any materials in separate sections (bottom of page)
        # This will add materials to topics that don't already have them from their sections
        self.extract_materials_with_fuzzy_matching(content, topics)

        return topics

    def extract_meeting(self, xml_file: Path) -> Optional[Meeting]:
        """Extract meeting data from XML file"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Define namespaces
            ns = {
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'wp': 'http://wordpress.org/export/1.2/',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }

            # Extract basic metadata
            title_elem = root.find('title')
            link_elem = root.find('link')
            post_id_elem = root.find('wp:post_id', ns)
            post_name_elem = root.find('wp:post_name', ns)
            post_date_elem = root.find('wp:post_date', ns)
            category_elem = root.find('category')
            creator_elem = root.find('dc:creator', ns)

            metadata = {
                'title': title_elem.text if title_elem is not None else '',
                'link': link_elem.text if link_elem is not None else '',
                'post_id': post_id_elem.text if post_id_elem is not None else '',
                'post_name': post_name_elem.text if post_name_elem is not None else '',
                'post_date': post_date_elem.text if post_date_elem is not None else '',
                'category': category_elem.text if category_elem is not None else '',
                'creator': creator_elem.text if creator_elem is not None else ''
            }

            # Extract custom fields
            custom_fields = []
            for postmeta in root.findall('wp:postmeta', ns):
                meta_key = postmeta.find('wp:meta_key', ns)
                meta_value = postmeta.find('wp:meta_value', ns)
                if meta_key is not None and meta_value is not None:
                    key = meta_key.text
                    if key in ['_thumbnail_id', 'stunnig_headers_bg_img']:
                        custom_fields.append({
                            'meta_key': key,
                            'meta_value': meta_value.text or ''
                        })

            # Extract content
            content_elem = root.find('content:encoded', ns)
            if content_elem is None or not content_elem.text:
                return None

            content = content_elem.text

            # Extract event date
            event_date = self.extract_event_date(content)

            # Extract topics using enhanced method
            topics = self.extract_topics_enhanced(content)

            return Meeting(
                metadata=metadata,
                custom_fields=custom_fields,
                event_date=event_date,
                topics=topics
            )

        except Exception as e:
            print(f"Error processing {xml_file.name}: {str(e)}")
            return None


def generate_structured_xml(meeting: Meeting, output_path: Path):
    """Generate clean structured XML"""
    root = ET.Element('meeting')

    # Metadata
    metadata_elem = ET.SubElement(root, 'metadata')
    for key, value in meeting.metadata.items():
        elem = ET.SubElement(metadata_elem, key)
        elem.text = value

    # Custom fields
    if meeting.custom_fields:
        custom_fields_elem = ET.SubElement(root, 'custom_fields')
        for field in meeting.custom_fields:
            field_elem = ET.SubElement(custom_fields_elem, 'field')
            for key, value in field.items():
                elem = ET.SubElement(field_elem, key)
                elem.text = value

    # Event
    event_elem = ET.SubElement(root, 'event')
    date_elem = ET.SubElement(event_elem, 'date')
    date_elem.text = meeting.event_date
    status_elem = ET.SubElement(event_elem, 'status')
    status_elem.text = 'ARCHIVED'

    # Topics
    topics_elem = ET.SubElement(root, 'topics')
    for topic in meeting.topics:
        topic_elem = ET.SubElement(topics_elem, 'topic', id=str(topic.id))

        # Speakers (can be multiple for panel sessions)
        if topic.speakers:
            speakers_elem = ET.SubElement(topic_elem, 'speakers')
            for speaker in topic.speakers:
                speaker_elem = ET.SubElement(speakers_elem, 'speaker')
                for key in ['name', 'title', 'photo_id', 'bio']:
                    value = getattr(speaker, key, '')
                    elem = ET.SubElement(speaker_elem, key)
                    elem.text = value

        # Presentation
        pres_elem = ET.SubElement(topic_elem, 'presentation')
        title_elem = ET.SubElement(pres_elem, 'title')
        title_elem.text = topic.presentation.title

        if topic.presentation.description:
            desc_elem = ET.SubElement(pres_elem, 'description')
            desc_elem.text = topic.presentation.description

        if topic.presentation.learning_outcomes:
            outcomes_elem = ET.SubElement(pres_elem, 'learning_outcomes')
            for outcome in topic.presentation.learning_outcomes:
                outcome_elem = ET.SubElement(outcomes_elem, 'outcome')
                outcome_elem.text = outcome

        # Materials
        if topic.materials:
            materials_elem = ET.SubElement(topic_elem, 'materials')
            for material in topic.materials:
                mat_elem = ET.SubElement(materials_elem, material.type)
                url_elem = ET.SubElement(mat_elem, 'url')
                url_elem.text = material.url
                label_elem = ET.SubElement(mat_elem, 'label')
                label_elem.text = material.label
                status_elem = ET.SubElement(mat_elem, 'status')
                status_elem.text = 'not_validated'

    # Write XML
    tree = ET.ElementTree(root)
    ET.indent(tree, space='  ')
    tree.write(output_path, encoding='utf-8', xml_declaration=True)


def generate_json(meeting: Meeting, output_path: Path):
    """Generate JSON output"""
    data = {
        'metadata': meeting.metadata,
        'custom_fields': meeting.custom_fields,
        'event': {
            'date': meeting.event_date,
            'status': 'ARCHIVED'
        },
        'topics': [
            {
                'id': topic.id,
                'speakers': [asdict(speaker) for speaker in topic.speakers],
                'presentation': asdict(topic.presentation),
                'materials': [asdict(m) for m in topic.materials]
            }
            for topic in meeting.topics
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def process_single_file(xml_file: Path, extractor: DataExtractor):
    """Process a single XML file"""
    print(f"\nProcessing: {xml_file.name}")
    print("=" * 80)

    meeting = extractor.extract_meeting(xml_file)
    if not meeting:
        print(f"❌ Failed to extract data")
        return None

    # Create output filenames
    base_name = xml_file.stem
    xml_output = OUTPUT_XML / f"{base_name}.xml"
    json_output = OUTPUT_JSON / f"{base_name}.json"

    # Generate outputs
    OUTPUT_XML.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.mkdir(parents=True, exist_ok=True)

    generate_structured_xml(meeting, xml_output)
    generate_json(meeting, json_output)

    # Print summary
    print(f"\n✓ Extracted {len(meeting.topics)} topics")
    for topic in meeting.topics:
        # Handle multiple speakers (e.g., panel sessions)
        if topic.speakers:
            if len(topic.speakers) == 1:
                speaker_name = topic.speakers[0].name
            else:
                speaker_names = [s.name for s in topic.speakers]
                speaker_name = f"Panel: {', '.join(speaker_names[:3])}"  # Show first 3
                if len(topic.speakers) > 3:
                    speaker_name += f" (+{len(topic.speakers) - 3} more)"
        else:
            speaker_name = "Joint/Unknown"

        print(f"  Topic {topic.id}: {speaker_name}")
        print(f"    Title: {topic.presentation.title[:60]}...")
        print(f"    Materials: {len(topic.materials)}")
        for material in topic.materials:
            print(f"      - {material.type}: {material.label}")

    print(f"\n✓ Generated: {xml_output.name}")
    print(f"✓ Generated: {json_output.name}")

    return meeting


def main():
    """Main execution"""
    print("=" * 80)
    print("ENHANCED XML DATA EXTRACTION - Version 2")
    print("=" * 80)
    print()

    # Check if specific file provided as argument
    if len(sys.argv) > 1:
        xml_file = INDIVIDUAL_POSTS / sys.argv[1]
        if not xml_file.exists():
            print(f"❌ File not found: {xml_file}")
            return

        extractor = DataExtractor()
        process_single_file(xml_file, extractor)
    else:
        print("Usage: python extract-structured-data-v2.py <filename.xml>")
        print("Example: python extract-structured-data-v2.py april-2021-webinar-meeting-archive-14812.xml")


if __name__ == '__main__':
    main()
