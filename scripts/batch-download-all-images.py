#!/usr/bin/env python3
"""
Batch Speaker Image Downloader
Processes all JSON files to download speaker images
"""

import json
import subprocess
from pathlib import Path
import time
import re

PROJECT_ROOT = Path(__file__).parent.parent
STRUCTURED_JSON = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-json'
REPORT_FILE = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'image-download-report.json'
SCRIPT_PATH = Path(__file__).parent / 'download-speaker-images.py'


def parse_output(output: str) -> tuple:
    """Parse script output to extract downloaded/failed counts"""
    downloaded = 0
    failed = 0

    # Look for "Summary: X downloaded, Y failed"
    summary_match = re.search(r'Summary:\s+(\d+)\s+downloaded,\s+(\d+)\s+failed', output)
    if summary_match:
        downloaded = int(summary_match.group(1))
        failed = int(summary_match.group(2))

    return downloaded, failed


def main():
    """Process all JSON files in batch"""
    print("=" * 80)
    print("BATCH SPEAKER IMAGE DOWNLOADER")
    print("=" * 80)
    print()

    # Find all JSON files with photo_ids
    print("Scanning for files with speaker photo_ids...")
    files_to_process = []

    for json_file in sorted(STRUCTURED_JSON.glob('*.json')):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if any topics have speakers with photo_ids
            has_photos = False
            for topic in data.get('topics', []):
                for speaker in topic.get('speakers', []):
                    if speaker.get('photo_id'):
                        has_photos = True
                        break
                if has_photos:
                    break

            if has_photos:
                files_to_process.append(json_file)
        except Exception as e:
            print(f"  ⚠ Error reading {json_file.name}: {e}")

    print(f"Found {len(files_to_process)} files to process")
    print()

    if not files_to_process:
        print("No files with photo_ids found!")
        return

    # Process each file
    results = {
        'total_files': len(files_to_process),
        'processed_files': 0,
        'total_images_downloaded': 0,
        'total_images_failed': 0,
        'files': []
    }

    for i, json_file in enumerate(files_to_process, 1):
        print(f"\n{'=' * 80}")
        print(f"[{i}/{len(files_to_process)}]")
        print(f"{'=' * 80}")

        try:
            # Run the download script for this file
            result = subprocess.run(
                ['python3', str(SCRIPT_PATH), json_file.name],
                capture_output=True,
                text=True,
                timeout=60
            )

            # Print the output
            print(result.stdout)

            if result.stderr and 'NotOpenSSLWarning' not in result.stderr:
                print("STDERR:", result.stderr)

            # Parse output to get counts
            downloaded, failed = parse_output(result.stdout)

            results['processed_files'] += 1
            results['total_images_downloaded'] += downloaded
            results['total_images_failed'] += failed

            results['files'].append({
                'filename': json_file.name,
                'status': 'success',
                'images_downloaded': downloaded,
                'images_failed': failed
            })

            # Small delay to be nice to the server
            time.sleep(2)

        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout processing file")
            results['files'].append({
                'filename': json_file.name,
                'status': 'error',
                'error': 'Timeout'
            })
        except Exception as e:
            print(f"  ❌ Error processing file: {e}")
            results['files'].append({
                'filename': json_file.name,
                'status': 'error',
                'error': str(e)
            })

    # Generate summary report
    print("\n" + "=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print(f"\nFiles processed: {results['processed_files']}/{results['total_files']}")
    print(f"Total images downloaded: {results['total_images_downloaded']}")
    print(f"Total images failed: {results['total_images_failed']}")

    # Show files with failures
    failed_files = [f for f in results['files'] if f.get('images_failed', 0) > 0 or f.get('status') == 'error']
    if failed_files:
        print(f"\n⚠ Files with issues ({len(failed_files)}):")
        for f in failed_files:
            if f['status'] == 'error':
                print(f"  - {f['filename']}: ERROR - {f.get('error', 'Unknown')}")
            else:
                print(f"  - {f['filename']}: {f['images_failed']} images failed")

    # Show success summary
    success_files = [f for f in results['files'] if f.get('status') == 'success' and f.get('images_downloaded', 0) > 0]
    if success_files:
        print(f"\n✓ Files with successful downloads ({len(success_files)}):")
        for f in success_files:
            print(f"  - {f['filename']}: {f['images_downloaded']} images")

    # Save report
    results['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Report saved to: {REPORT_FILE}")
    print()


if __name__ == '__main__':
    main()
