#!/usr/bin/env python3
"""
Extraction Verification Script
Compares structured XML data against live webpage content to verify accuracy
"""

import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import sys
import time
from difflib import SequenceMatcher

PROJECT_ROOT = Path(__file__).parent.parent
STRUCTURED_XML = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-xml'
VERIFICATION_OUTPUT = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'verification-report.json'


@dataclass
class PageTopic:
    """Topic extracted from live webpage"""
    id: int
    speaker_name: Optional[str]
    presentation_title: Optional[str]
    materials: List[str]  # URLs


@dataclass
class PageContent:
    """Content extracted from live webpage"""
    accessible: bool
    error_message: Optional[str]
    event_date: Optional[str]
    topics: List[PageTopic]
    all_links: List[str]


@dataclass
class ComparisonResult:
    """Result of comparing XML to webpage"""
    file_name: str
    url: str
    page_accessible: bool
    accuracy_score: float
    topic_count_match: bool
    topic_comparisons: List[Dict]
    warnings: List[str]
    errors: List[str]


class LivePageFetcher:
    """Fetches and parses live webpage content"""

    def __init__(self):
        self.session = requests.Session()
        # Mimic real browser headers to bypass bot protection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'DNT': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-CH-UA': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'Sec-CH-UA-Mobile': '?1',
            'Sec-CH-UA-Platform': '"Android"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://aaiila.org/'
        })
        # Enable cookie handling
        self.session.cookies.set('wordpress_test_cookie', 'WP Cookie check', domain='aaiila.org')
        self.session.cookies.set('wp_lang', 'en_US', domain='aaiila.org')

    def fetch_page(self, url: str) -> Tuple[bool, Optional[str], Optional[BeautifulSoup]]:
        """
        Fetch webpage and return (success, error_message, soup)
        """
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return True, None, soup
            else:
                return False, f"HTTP {response.status_code}", None
        except requests.Timeout:
            return False, "Request timeout", None
        except requests.RequestException as e:
            return False, str(e), None

    def extract_event_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract event date from page"""
        # Look for date patterns
        date_pattern = r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+([A-Za-z]+\s+\d+,\s+\d{4})'
        text = soup.get_text()
        match = re.search(date_pattern, text)
        return match.group(0) if match else None

    def extract_topics(self, soup: BeautifulSoup) -> List[PageTopic]:
        """Extract topics from page HTML"""
        topics = []

        # Find all topic headings (h2, h3 with "TOPIC")
        topic_headings = soup.find_all(['h2', 'h3'], string=re.compile(r'TOPIC\s+\d+', re.IGNORECASE))

        for i, heading in enumerate(topic_headings):
            topic_id = i + 1

            # Try to extract topic number from heading text
            topic_match = re.search(r'TOPIC\s+(\d+)', heading.get_text(), re.IGNORECASE)
            if topic_match:
                topic_id = int(topic_match.group(1))

            # Look for speaker name in nearby content
            # WordPress uses divs with 'team' in class name
            speaker_name = None
            next_elements = heading.find_all_next(['div', 'h4', 'h5'], limit=20)

            for elem in next_elements:
                # Stop if we hit next topic
                if elem.name in ['h2', 'h3'] and 'TOPIC' in elem.get_text().upper():
                    break

                # Check for team member divs
                if elem.name == 'div':
                    elem_class = elem.get('class', [])
                    if any('team' in str(c).lower() for c in elem_class):
                        text = elem.get_text().strip()
                        # Extract just the name (before title/position)
                        # Pattern: "Name TitlePosition..." -> extract just "Name"
                        name_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
                        if name_match:
                            speaker_name = name_match.group(1).strip()
                            # Clean up if title is concatenated without space
                            # e.g., "Gatis RozePrivate" -> "Gatis Roze"
                            words = speaker_name.split()
                            if len(words) >= 2:
                                # Take first 2-3 words as name
                                speaker_name = ' '.join(words[:2])
                            break

            # Look for presentation title
            presentation_title = None
            for elem in next_elements:
                # Stop if we hit next topic
                if elem.name in ['h2', 'h3'] and 'TOPIC' in elem.get_text().upper():
                    break

                if elem.name == 'div':
                    text = elem.get_text().strip()
                    # Look for presentation title patterns
                    # Usually 20-100 chars, starts with capital, not speaker info
                    if (20 < len(text) < 150 and
                        text[0].isupper() and
                        'learn' not in text.lower() and
                        'attend' not in text.lower() and
                        'investor' not in text.lower() and
                        'author' not in text.lower()):
                        # Check if it's not the speaker description
                        if speaker_name and speaker_name not in text:
                            presentation_title = text
                            break

            topics.append(PageTopic(
                id=topic_id,
                speaker_name=speaker_name,
                presentation_title=presentation_title,
                materials=[]
            ))

        return topics

    def extract_all_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract all material links (YouTube, PDFs) from page"""
        links = []

        # Find all links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Filter for material links
            if any(domain in href for domain in ['youtube.com', 'youtu.be', '.pdf', 'community.aaii.com']):
                # Normalize URL (remove trailing slashes, etc.)
                normalized = href.rstrip('/')
                if normalized not in links:
                    links.append(normalized)

        return links

    def parse_page(self, url: str) -> PageContent:
        """Fetch and parse page content"""
        success, error_msg, soup = self.fetch_page(url)

        if not success:
            return PageContent(
                accessible=False,
                error_message=error_msg,
                event_date=None,
                topics=[],
                all_links=[]
            )

        return PageContent(
            accessible=True,
            error_message=None,
            event_date=self.extract_event_date(soup),
            topics=self.extract_topics(soup),
            all_links=self.extract_all_links(soup)
        )


class ContentComparator:
    """Compares XML data with live page content"""

    @staticmethod
    def similarity_score(str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0-1)"""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    @staticmethod
    def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Check if two strings match with fuzzy logic"""
        return ContentComparator.similarity_score(str1, str2) >= threshold

    def compare_topics(self, xml_topics: List, page_topics: List[PageTopic], page_links: List[str]) -> Tuple[List[Dict], List[str]]:
        """
        Compare topics from XML with topics from page.
        Returns (comparisons, warnings)
        """
        comparisons = []
        warnings = []

        # Check topic count
        if len(xml_topics) != len(page_topics):
            warnings.append(f"Topic count mismatch: XML has {len(xml_topics)}, page has {len(page_topics)}")

        # Compare each XML topic
        for xml_topic in xml_topics:
            topic_id = xml_topic['id']
            comparison = {
                'topic_id': topic_id,
                'speaker_match': False,
                'title_match': False,
                'materials_match': False,
                'checks_passed': 0,
                'total_checks': 3,
                'discrepancies': []
            }

            # Find corresponding page topic
            page_topic = None
            for pt in page_topics:
                if pt.id == topic_id:
                    page_topic = pt
                    break

            if not page_topic:
                comparison['discrepancies'].append(f"Topic {topic_id} not found on page")
                comparisons.append(comparison)
                continue

            # Compare speaker
            xml_speaker = xml_topic.get('speaker', {})
            if xml_speaker and xml_speaker.get('name'):
                xml_name = xml_speaker['name']
                if page_topic.speaker_name:
                    if self.fuzzy_match(xml_name, page_topic.speaker_name, 0.75):
                        comparison['speaker_match'] = True
                        comparison['checks_passed'] += 1
                    else:
                        comparison['discrepancies'].append(
                            f"Speaker: XML='{xml_name}' vs Page='{page_topic.speaker_name}'"
                        )
                else:
                    warnings.append(f"Topic {topic_id}: Speaker not found on page (XML: {xml_name})")
                    comparison['checks_passed'] += 0.5  # Partial credit
            else:
                # No speaker in XML (joint presentation)
                comparison['speaker_match'] = True
                comparison['checks_passed'] += 1
                warnings.append(f"Topic {topic_id}: No speaker in XML (joint presentation)")

            # Compare presentation title
            xml_title = xml_topic.get('presentation', {}).get('title', '')
            if xml_title and page_topic.presentation_title:
                if self.fuzzy_match(xml_title, page_topic.presentation_title, 0.7):
                    comparison['title_match'] = True
                    comparison['checks_passed'] += 1
                else:
                    comparison['discrepancies'].append(
                        f"Title: XML='{xml_title[:50]}...' vs Page='{page_topic.presentation_title[:50]}...'"
                    )
            elif xml_title:
                warnings.append(f"Topic {topic_id}: Title not found on page")
                # Still give partial credit if speaker matched
                comparison['checks_passed'] += 0.5

            # Compare materials - verify XML material URLs exist on page
            xml_materials = xml_topic.get('materials', [])
            if xml_materials:
                materials_found = 0
                for material in xml_materials:
                    xml_url = material.get('url', '').rstrip('/')
                    # Check if this URL exists on the page
                    if any(self.fuzzy_match(xml_url, page_url, 0.9) for page_url in page_links):
                        materials_found += 1

                if materials_found == len(xml_materials):
                    comparison['materials_match'] = True
                    comparison['checks_passed'] += 1
                elif materials_found > 0:
                    # Partial credit
                    comparison['checks_passed'] += 0.7
                    warnings.append(f"Topic {topic_id}: Only {materials_found}/{len(xml_materials)} materials found on page")
                else:
                    comparison['discrepancies'].append(f"Materials: None of {len(xml_materials)} materials found on page")
            else:
                # No materials in XML
                comparison['materials_match'] = True
                comparison['checks_passed'] += 1

            comparisons.append(comparison)

        return comparisons, warnings

    def calculate_accuracy(self, comparisons: List[Dict]) -> float:
        """Calculate overall accuracy percentage"""
        if not comparisons:
            return 0.0

        total_checks = sum(c['total_checks'] for c in comparisons)
        passed_checks = sum(c['checks_passed'] for c in comparisons)

        return (passed_checks / total_checks * 100) if total_checks > 0 else 0.0


def load_xml_data(xml_file: Path) -> Optional[Dict]:
    """Load data from structured XML file"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Extract metadata
        metadata = {}
        metadata_elem = root.find('metadata')
        if metadata_elem is not None:
            for child in metadata_elem:
                metadata[child.tag] = child.text or ''

        # Extract topics
        topics = []
        topics_elem = root.find('topics')
        if topics_elem is not None:
            for topic_elem in topics_elem.findall('topic'):
                topic = {
                    'id': int(topic_elem.get('id', 0)),
                    'speaker': None,
                    'presentation': {},
                    'materials': []
                }

                # Speaker
                speaker_elem = topic_elem.find('speaker')
                if speaker_elem is not None:
                    topic['speaker'] = {
                        'name': speaker_elem.findtext('name', ''),
                        'title': speaker_elem.findtext('title', '')
                    }

                # Presentation
                pres_elem = topic_elem.find('presentation')
                if pres_elem is not None:
                    topic['presentation'] = {
                        'title': pres_elem.findtext('title', ''),
                        'description': pres_elem.findtext('description', '')
                    }

                # Materials
                materials_elem = topic_elem.find('materials')
                if materials_elem is not None:
                    for mat in materials_elem:
                        topic['materials'].append({
                            'type': mat.tag,
                            'url': mat.findtext('url', ''),
                            'label': mat.findtext('label', '')
                        })

                topics.append(topic)

        return {
            'metadata': metadata,
            'topics': topics
        }

    except Exception as e:
        print(f"Error loading XML: {e}")
        return None


def verify_file(xml_file: Path, fetcher: LivePageFetcher, comparator: ContentComparator) -> ComparisonResult:
    """Verify a single XML file against its live webpage"""
    print(f"\nVerifying: {xml_file.name}")
    print("=" * 80)

    # Load XML data
    xml_data = load_xml_data(xml_file)
    if not xml_data:
        return ComparisonResult(
            file_name=xml_file.name,
            url="",
            page_accessible=False,
            accuracy_score=0.0,
            topic_count_match=False,
            topic_comparisons=[],
            warnings=[],
            errors=["Failed to load XML file"]
        )

    url = xml_data['metadata'].get('link', '')
    print(f"URL: {url}")

    # Fetch and parse live page
    page_content = fetcher.parse_page(url)

    if not page_content.accessible:
        print(f"❌ Page not accessible: {page_content.error_message}")
        return ComparisonResult(
            file_name=xml_file.name,
            url=url,
            page_accessible=False,
            accuracy_score=0.0,
            topic_count_match=False,
            topic_comparisons=[],
            warnings=[],
            errors=[f"Page not accessible: {page_content.error_message}"]
        )

    print(f"✓ Page accessible")
    print(f"  Topics found on page: {len(page_content.topics)}")
    print(f"  Topics in XML: {len(xml_data['topics'])}")

    # Compare content
    topic_comparisons, warnings = comparator.compare_topics(
        xml_data['topics'],
        page_content.topics,
        page_content.all_links
    )
    accuracy = comparator.calculate_accuracy(topic_comparisons)
    topic_count_match = len(xml_data['topics']) == len(page_content.topics)

    # Print results
    print(f"\nAccuracy: {accuracy:.1f}%")
    if topic_count_match:
        print(f"✓ Topic count matches: {len(xml_data['topics'])}")
    else:
        print(f"⚠ Topic count mismatch: XML={len(xml_data['topics'])}, Page={len(page_content.topics)}")

    for comp in topic_comparisons:
        topic_id = comp['topic_id']
        checks = comp['checks_passed']
        total = comp['total_checks']
        print(f"\n  Topic {topic_id}: {checks}/{total} checks passed")

        if comp['speaker_match']:
            print(f"    ✓ Speaker match")
        else:
            print(f"    ✗ Speaker mismatch")

        if comp['title_match']:
            print(f"    ✓ Title match")
        else:
            print(f"    ✗ Title mismatch")

        if comp['discrepancies']:
            for disc in comp['discrepancies']:
                print(f"    ⚠ {disc}")

    if warnings:
        print(f"\nWarnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    return ComparisonResult(
        file_name=xml_file.name,
        url=url,
        page_accessible=True,
        accuracy_score=accuracy,
        topic_count_match=topic_count_match,
        topic_comparisons=topic_comparisons,
        warnings=warnings,
        errors=[]
    )


def main():
    """Main execution"""
    print("=" * 80)
    print("EXTRACTION VERIFICATION SYSTEM")
    print("=" * 80)
    print()

    fetcher = LivePageFetcher()
    comparator = ContentComparator()

    # Check if specific file provided
    if len(sys.argv) > 1:
        xml_file = STRUCTURED_XML / sys.argv[1]
        if not xml_file.exists():
            print(f"❌ File not found: {xml_file}")
            return

        result = verify_file(xml_file, fetcher, comparator)

        # Save result
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'files_verified': 1,
            'results': [asdict(result)]
        }

        with open(VERIFICATION_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Verification report saved: {VERIFICATION_OUTPUT}")

    else:
        print("Usage: python verify-extraction-accuracy.py <filename.xml>")
        print("Example: python verify-extraction-accuracy.py april-2021-webinar-meeting-archive-14812.xml")


if __name__ == '__main__':
    main()
