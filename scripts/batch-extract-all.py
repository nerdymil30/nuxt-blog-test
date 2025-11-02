#!/usr/bin/env python3
"""
Batch Extraction Script
Runs V2 extraction on all 50 XML files
"""

import sys
from pathlib import Path
import time
import importlib.util

# Load the V2 extraction script
PROJECT_ROOT = Path(__file__).parent.parent
v2_script = PROJECT_ROOT / 'scripts' / 'extract-structured-data-v2.py'

spec = importlib.util.spec_from_file_location("extract_v2", v2_script)
extract_v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_v2)

DataExtractor = extract_v2.DataExtractor
process_single_file = extract_v2.process_single_file

INDIVIDUAL_POSTS = PROJECT_ROOT / 'AAII-Migration-assets' / 'individual-posts' / 'monthly-meetings'


def main():
    """Process all XML files"""
    print("=" * 80)
    print("BATCH V2 EXTRACTION - ALL 50 FILES")
    print("=" * 80)
    print()

    # Get all XML files
    xml_files = sorted(INDIVIDUAL_POSTS.glob('*.xml'))

    print(f"Found {len(xml_files)} XML files to process")
    print()

    extractor = DataExtractor()
    results = {
        'success': [],
        'failed': [],
        'total': len(xml_files)
    }

    start_time = time.time()

    # Process each file
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n[{i}/{len(xml_files)}] Processing {xml_file.name}")
        print("-" * 80)

        try:
            meeting = process_single_file(xml_file, extractor)
            if meeting:
                results['success'].append(xml_file.name)
            else:
                results['failed'].append(xml_file.name)
        except Exception as e:
            print(f"❌ Error: {e}")
            results['failed'].append(xml_file.name)

        # Brief pause between requests
        if i < len(xml_files):
            time.sleep(0.5)

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print("BATCH EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"\nTotal files: {results['total']}")
    print(f"✓ Success: {len(results['success'])}")
    print(f"✗ Failed: {len(results['failed'])}")
    print(f"Time elapsed: {elapsed:.1f} seconds")

    if results['failed']:
        print(f"\nFailed files:")
        for filename in results['failed']:
            print(f"  - {filename}")

    print(f"\n✓ Extraction complete!")
    print(f"✓ Structured XML files: AAII-Migration-assets/output/structured-xml/")
    print(f"✓ JSON files: AAII-Migration-assets/output/structured-json/")


if __name__ == '__main__':
    main()
