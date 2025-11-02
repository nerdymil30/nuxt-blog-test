#!/usr/bin/env python3
"""
Speaker Image Downloader
Downloads speaker images from live webpages and updates structured data with local paths
"""

import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import time
from urllib.parse import urljoin, urlparse
import hashlib

PROJECT_ROOT = Path(__file__).parent.parent
STRUCTURED_JSON = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-json'
STRUCTURED_XML = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-xml'
IMAGES_DIR = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'assets' / 'images'


class LivePageFetcher:
    """Fetches live webpage content with proper headers"""

    def __init__(self):
        self.session = requests.Session()
        # Mimic real browser headers (from verify-extraction-accuracy.py)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Cache-Control': 'no-cache',
            'Referer': 'https://aaiila.org/'
        })

    def fetch_page(self, url: str) -> Tuple[bool, Optional[BeautifulSoup]]:
        """Fetch webpage and return (success, soup)"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return True, soup
            else:
                print(f"  ⚠ HTTP {response.status_code}")
                return False, None
        except requests.Timeout:
            print(f"  ⚠ Request timeout")
            return False, None
        except requests.RequestException as e:
            print(f"  ⚠ Request error: {e}")
            return False, None

    def download_image(self, image_url: str, output_path: Path) -> bool:
        """Download image from URL to local path"""
        try:
            response = self.session.get(image_url, timeout=15)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"    ⚠ Failed to download: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"    ⚠ Download error: {e}")
            return False


class ImageExtractor:
    """Extracts speaker image URLs from webpage HTML"""

    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to URL-friendly slug"""
        text = text.lower().strip()
        # Remove special characters except spaces and hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        # Replace spaces with hyphens
        text = re.sub(r'[-\s]+', '-', text)
        return text

    def find_speaker_images(self, soup: BeautifulSoup, speaker_data: List[Tuple[str, str]]) -> Dict[str, str]:
        """
        Find speaker image URLs from HTML by matching speaker names.
        speaker_data: List of (photo_id, speaker_name) tuples
        Returns dict: {photo_id: image_url}
        """
        image_map = {}

        # Get all image tags
        all_imgs = soup.find_all('img')

        # Strategy 1: Match by speaker name in image filename/URL
        for photo_id, speaker_name in speaker_data:
            if photo_id in image_map:
                continue

            # Create name variations to search for
            name_lower = speaker_name.lower()
            name_parts = name_lower.split()

            # Try matching full name with underscore
            name_slug = name_lower.replace(' ', '_').replace('.', '').replace(',', '')

            # Try matching with hyphen
            name_dash = name_lower.replace(' ', '-').replace('.', '').replace(',', '')

            for img in all_imgs:
                src = img.get('src', '').lower()

                # Check if any name variation is in the image URL
                if (name_slug in src or
                    name_dash in src or
                    (len(name_parts) >= 2 and name_parts[0] in src and name_parts[-1] in src)):

                    # Use the actual src (not lowercased)
                    actual_src = img.get('src', '')
                    if actual_src:
                        image_map[photo_id] = actual_src
                        break

        # Strategy 2: Find images near speaker name in HTML structure
        for photo_id, speaker_name in speaker_data:
            if photo_id in image_map:
                continue

            # Find text nodes containing speaker name
            text_elements = soup.find_all(string=re.compile(re.escape(speaker_name), re.IGNORECASE))

            for text_elem in text_elements:
                parent = text_elem.parent
                if not parent:
                    continue

                # Search parent and ancestors for img tags
                current = parent
                for _ in range(5):  # Search up to 5 levels up
                    if current is None:
                        break

                    img = current.find('img')
                    if img:
                        src = img.get('src')
                        if src:
                            image_map[photo_id] = src
                            break

                    current = current.parent

                if photo_id in image_map:
                    break

        # Strategy 3: Find images with WordPress attachment class (wp-image-{id})
        # This is less reliable but kept as fallback
        for photo_id, speaker_name in speaker_data:
            if photo_id in image_map:
                continue

            img_tags = soup.find_all('img', class_=re.compile(f'wp-image-{photo_id}'))
            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                if src:
                    image_map[photo_id] = src
                    break

        return image_map


class DataUpdater:
    """Updates structured JSON and XML files with local image paths"""

    @staticmethod
    def update_json(json_file: Path, image_updates: Dict[int, str]) -> bool:
        """
        Update JSON file with local image paths.
        image_updates: {topic_id: {speaker_index: local_path}}
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update speaker photo paths
            for topic in data.get('topics', []):
                topic_id = topic['id']
                if topic_id in image_updates:
                    for speaker_idx, local_path in image_updates[topic_id].items():
                        if speaker_idx < len(topic.get('speakers', [])):
                            topic['speakers'][speaker_idx]['photo_local_path'] = local_path

            # Write back
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"  ⚠ Error updating JSON: {e}")
            return False

    @staticmethod
    def update_xml(xml_file: Path, image_updates: Dict[int, str]) -> bool:
        """
        Update XML file with local image paths.
        image_updates: {topic_id: {speaker_index: local_path}}
        """
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            topics_elem = root.find('topics')
            if topics_elem is None:
                return False

            for topic_elem in topics_elem.findall('topic'):
                topic_id = int(topic_elem.get('id', 0))

                if topic_id in image_updates:
                    speakers_elem = topic_elem.find('speakers')
                    if speakers_elem is not None:
                        speaker_elems = speakers_elem.findall('speaker')

                        for speaker_idx, local_path in image_updates[topic_id].items():
                            if speaker_idx < len(speaker_elems):
                                speaker_elem = speaker_elems[speaker_idx]

                                # Add photo_local_path element after photo_id
                                photo_local_elem = ET.Element('photo_local_path')
                                photo_local_elem.text = local_path

                                # Find position to insert (after photo_id)
                                photo_id_elem = speaker_elem.find('photo_id')
                                if photo_id_elem is not None:
                                    idx = list(speaker_elem).index(photo_id_elem)
                                    speaker_elem.insert(idx + 1, photo_local_elem)
                                else:
                                    speaker_elem.append(photo_local_elem)

            # Write back with formatting
            ET.indent(tree, space='  ')
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)

            return True
        except Exception as e:
            print(f"  ⚠ Error updating XML: {e}")
            return False


def process_file(json_file: Path, fetcher: LivePageFetcher, extractor: ImageExtractor, updater: DataUpdater) -> Tuple[int, int]:
    """
    Process a single JSON file to download speaker images.
    Returns (images_downloaded, images_failed)
    """
    print(f"\nProcessing: {json_file.name}")
    print("=" * 80)

    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ❌ Failed to load JSON: {e}")
        return 0, 0

    url = data['metadata'].get('link', '')
    print(f"  URL: {url}")

    # Fetch page
    success, soup = fetcher.fetch_page(url)
    if not success:
        print(f"  ❌ Failed to fetch page")
        return 0, 0

    print(f"  ✓ Page fetched")

    # Collect all photo_ids and speaker info
    photo_id_to_speaker = {}  # {photo_id: (topic_id, speaker_idx, speaker_name)}

    for topic in data.get('topics', []):
        topic_id = topic['id']
        for speaker_idx, speaker in enumerate(topic.get('speakers', [])):
            photo_id = speaker.get('photo_id', '')
            if photo_id:
                speaker_name = speaker.get('name', 'unknown')
                photo_id_to_speaker[photo_id] = (topic_id, speaker_idx, speaker_name)

    if not photo_id_to_speaker:
        print(f"  ℹ No speakers with photo_id found")
        return 0, 0

    print(f"  Found {len(photo_id_to_speaker)} speakers with photo_ids")

    # Extract image URLs from page
    # Create list of (photo_id, speaker_name) tuples
    speaker_data = [(photo_id, info[2]) for photo_id, info in photo_id_to_speaker.items()]
    image_map = extractor.find_speaker_images(soup, speaker_data)

    print(f"  Found {len(image_map)} image URLs on page")

    # Download images
    images_downloaded = 0
    images_failed = 0
    image_updates = {}  # {topic_id: {speaker_idx: local_path}}

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    for photo_id, image_url in image_map.items():
        topic_id, speaker_idx, speaker_name = photo_id_to_speaker[photo_id]

        # Create filename: {speaker-slug}_{photo_id}.{ext}
        speaker_slug = extractor.slugify(speaker_name)
        ext = Path(urlparse(image_url).path).suffix or '.jpg'
        filename = f"{speaker_slug}_{photo_id}{ext}"
        output_path = IMAGES_DIR / filename
        local_path = f"assets/images/{filename}"

        print(f"\n  Downloading: {speaker_name}")
        print(f"    Photo ID: {photo_id}")
        print(f"    URL: {image_url[:80]}...")
        print(f"    Saving to: {filename}")

        # Download
        if fetcher.download_image(image_url, output_path):
            print(f"    ✓ Downloaded ({output_path.stat().st_size} bytes)")
            images_downloaded += 1

            # Track for updating structured data
            if topic_id not in image_updates:
                image_updates[topic_id] = {}
            image_updates[topic_id][speaker_idx] = local_path
        else:
            print(f"    ❌ Download failed")
            images_failed += 1

    # Update structured data files
    if image_updates:
        print(f"\n  Updating structured data files...")

        # Update JSON
        if updater.update_json(json_file, image_updates):
            print(f"    ✓ Updated JSON: {json_file.name}")

        # Update XML
        xml_file = STRUCTURED_XML / json_file.name.replace('.json', '.xml')
        if xml_file.exists():
            if updater.update_xml(xml_file, image_updates):
                print(f"    ✓ Updated XML: {xml_file.name}")

    print(f"\n  Summary: {images_downloaded} downloaded, {images_failed} failed")

    return images_downloaded, images_failed


def main():
    """Main execution"""
    print("=" * 80)
    print("SPEAKER IMAGE DOWNLOADER")
    print("=" * 80)
    print()

    fetcher = LivePageFetcher()
    extractor = ImageExtractor()
    updater = DataUpdater()

    # Check if specific file provided
    if len(sys.argv) > 1:
        json_filename = sys.argv[1]
        if not json_filename.endswith('.json'):
            json_filename += '.json'

        json_file = STRUCTURED_JSON / json_filename
        if not json_file.exists():
            print(f"❌ File not found: {json_file}")
            return

        downloaded, failed = process_file(json_file, fetcher, extractor, updater)

        print(f"\n{'=' * 80}")
        print(f"COMPLETE: {downloaded} images downloaded, {failed} failed")
        print(f"{'=' * 80}")

    else:
        print("Usage: python download-speaker-images.py <filename.json>")
        print("Example: python download-speaker-images.py april-2024-skirballwebinar-archive-16632.json")


if __name__ == '__main__':
    main()
