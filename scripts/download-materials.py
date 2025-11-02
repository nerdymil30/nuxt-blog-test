#!/usr/bin/env python3
"""
Materials Downloader (PDF/PPT)
Downloads presentation materials from live webpages and updates structured data with local paths
"""

import xml.etree.ElementTree as ET
import requests
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import time
from urllib.parse import urlparse
import hashlib

PROJECT_ROOT = Path(__file__).parent.parent
STRUCTURED_JSON = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-json'
STRUCTURED_XML = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-xml'
MATERIALS_DIR = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'assets' / 'materials'


class MaterialsFetcher:
    """Fetches materials (PDF/PPT) from URLs with proper headers"""

    def __init__(self):
        self.session = requests.Session()
        # Mimic real browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/pdf,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Cache-Control': 'no-cache',
            'Referer': 'https://aaiila.org/'
        })

    def download_material(self, material_url: str, output_path: Path) -> bool:
        """Download material from URL to local path"""
        try:
            response = self.session.get(material_url, timeout=30)
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


class DataUpdater:
    """Updates structured JSON and XML files with local material paths"""

    @staticmethod
    def update_json(json_file: Path, material_updates: Dict[int, List[Dict]]) -> bool:
        """
        Update JSON file with local material paths.
        material_updates: {topic_id: [{material_index: int, local_path: str}]}
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update material paths
            for topic in data.get('topics', []):
                topic_id = topic['id']
                if topic_id in material_updates:
                    for update in material_updates[topic_id]:
                        material_idx = update['material_index']
                        local_path = update['local_path']

                        if material_idx < len(topic.get('materials', [])):
                            topic['materials'][material_idx]['local_path'] = local_path

            # Write back
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"  ⚠ Error updating JSON: {e}")
            return False

    @staticmethod
    def update_xml(xml_file: Path, material_updates: Dict[int, List[Dict]]) -> bool:
        """
        Update XML file with local material paths.
        material_updates: {topic_id: [{material_index: int, local_path: str}]}
        """
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            topics_elem = root.find('topics')
            if topics_elem is None:
                return False

            for topic_elem in topics_elem.findall('topic'):
                topic_id = int(topic_elem.get('id', 0))

                if topic_id in material_updates:
                    materials_elem = topic_elem.find('materials')
                    if materials_elem is not None:
                        # XML uses type-specific tags: <recording>, <slides>, etc.
                        # Get all material child elements in order
                        material_elems = list(materials_elem)

                        for update in material_updates[topic_id]:
                            material_idx = update['material_index']
                            local_path = update['local_path']

                            if material_idx < len(material_elems):
                                material_elem = material_elems[material_idx]

                                # Add local_path element
                                local_path_elem = ET.Element('local_path')
                                local_path_elem.text = local_path

                                # Append to material element
                                material_elem.append(local_path_elem)

            # Write back with formatting
            ET.indent(tree, space='  ')
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)

            return True
        except Exception as e:
            print(f"  ⚠ Error updating XML: {e}")
            return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be filesystem-safe"""
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:200] + ('.' + ext if ext else '')
    return filename


def process_file(json_file: Path, fetcher: MaterialsFetcher, updater: DataUpdater) -> Tuple[int, int]:
    """
    Process a single JSON file to download materials.
    Returns (materials_downloaded, materials_failed)
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

    # Collect all materials that are PDFs or PPTs
    downloadable_materials = []  # [(topic_id, material_idx, material_obj)]

    for topic in data.get('topics', []):
        topic_id = topic['id']
        for material_idx, material in enumerate(topic.get('materials', [])):
            mat_type = material.get('type', '')
            url = material.get('url', '')

            # Only download PDF/PPT files (skip recordings)
            if mat_type == 'slides' or '.pdf' in url.lower() or '.ppt' in url.lower():
                downloadable_materials.append((topic_id, material_idx, material))

    if not downloadable_materials:
        print(f"  ℹ No downloadable materials found (PDFs/PPTs)")
        return 0, 0

    print(f"  Found {len(downloadable_materials)} downloadable materials")

    # Download materials
    materials_downloaded = 0
    materials_failed = 0
    material_updates = {}  # {topic_id: [{material_index: int, local_path: str}]}

    MATERIALS_DIR.mkdir(parents=True, exist_ok=True)

    for topic_id, material_idx, material in downloadable_materials:
        url = material.get('url', '')
        label = material.get('label', 'material')

        # Extract filename from URL
        parsed_url = urlparse(url)
        original_filename = Path(parsed_url.path).name

        # If no filename, generate one
        if not original_filename or '.' not in original_filename:
            ext = '.pdf' if '.pdf' in url.lower() else '.ppt'
            original_filename = f"material_{topic_id}_{material_idx}{ext}"

        # Sanitize filename
        filename = sanitize_filename(original_filename)
        output_path = MATERIALS_DIR / filename
        local_path = f"assets/materials/{filename}"

        print(f"\n  Downloading: {label}")
        print(f"    Topic ID: {topic_id}")
        print(f"    URL: {url[:80]}...")
        print(f"    Saving to: {filename}")

        # Download
        if fetcher.download_material(url, output_path):
            print(f"    ✓ Downloaded ({output_path.stat().st_size} bytes)")
            materials_downloaded += 1

            # Track for updating structured data
            if topic_id not in material_updates:
                material_updates[topic_id] = []
            material_updates[topic_id].append({
                'material_index': material_idx,
                'local_path': local_path
            })
        else:
            print(f"    ❌ Download failed")
            materials_failed += 1

    # Update structured data files
    if material_updates:
        print(f"\n  Updating structured data files...")

        # Update JSON
        if updater.update_json(json_file, material_updates):
            print(f"    ✓ Updated JSON: {json_file.name}")

        # Update XML
        xml_file = STRUCTURED_XML / json_file.name.replace('.json', '.xml')
        if xml_file.exists():
            if updater.update_xml(xml_file, material_updates):
                print(f"    ✓ Updated XML: {xml_file.name}")

    print(f"\n  Summary: {materials_downloaded} downloaded, {materials_failed} failed")

    return materials_downloaded, materials_failed


def main():
    """Main execution"""
    print("=" * 80)
    print("MATERIALS DOWNLOADER (PDF/PPT)")
    print("=" * 80)
    print()

    fetcher = MaterialsFetcher()
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

        downloaded, failed = process_file(json_file, fetcher, updater)

        print(f"\n{'=' * 80}")
        print(f"COMPLETE: {downloaded} materials downloaded, {failed} failed")
        print(f"{'=' * 80}")

    else:
        print("Usage: python download-materials.py <filename.json>")
        print("Example: python download-materials.py april-2021-webinar-meeting-archive-14812.json")


if __name__ == '__main__':
    main()
