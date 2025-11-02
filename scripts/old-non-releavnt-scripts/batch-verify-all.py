#!/usr/bin/env python3
"""
Batch Verification Script
Runs web verification on all 50 structured XML files
"""

import sys
from pathlib import Path
import time
import json
import importlib.util

# Load the verification script
PROJECT_ROOT = Path(__file__).parent.parent
verify_script = PROJECT_ROOT / 'scripts' / 'verify-extraction-accuracy.py'

spec = importlib.util.spec_from_file_location("verify", verify_script)
verify_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_module)

LivePageFetcher = verify_module.LivePageFetcher
ContentComparator = verify_module.ContentComparator
verify_file = verify_module.verify_file
load_xml_data = verify_module.load_xml_data

STRUCTURED_XML = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'structured-xml'
VERIFICATION_OUTPUT = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'batch-verification-report.json'


def main():
    """Verify all structured XML files"""
    print("=" * 80)
    print("BATCH WEB VERIFICATION - ALL 50 FILES")
    print("=" * 80)
    print()

    # Get all structured XML files
    xml_files = sorted(STRUCTURED_XML.glob('*.xml'))

    print(f"Found {len(xml_files)} structured XML files to verify")
    print()

    fetcher = LivePageFetcher()
    comparator = ContentComparator()

    results = []
    stats = {
        'total': len(xml_files),
        'accessible': 0,
        'inaccessible': 0,
        'topic_matches': 0,
        'total_accuracy': 0.0,
        'high_accuracy': 0,  # >= 80%
        'medium_accuracy': 0,  # 50-79%
        'low_accuracy': 0,  # < 50%
    }

    start_time = time.time()

    # Verify each file
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n[{i}/{len(xml_files)}] {xml_file.name}")
        print("-" * 60)

        try:
            result = verify_file(xml_file, fetcher, comparator)
            results.append(result)

            # Update stats
            if result.page_accessible:
                stats['accessible'] += 1
                stats['total_accuracy'] += result.accuracy_score

                if result.accuracy_score >= 80:
                    stats['high_accuracy'] += 1
                elif result.accuracy_score >= 50:
                    stats['medium_accuracy'] += 1
                else:
                    stats['low_accuracy'] += 1

                if result.topic_count_match:
                    stats['topic_matches'] += 1
            else:
                stats['inaccessible'] += 1

        except Exception as e:
            print(f"❌ Verification error: {e}")
            results.append({
                'file_name': xml_file.name,
                'error': str(e)
            })

        # Brief pause between requests to be respectful to server
        if i < len(xml_files):
            time.sleep(1.5)

    # Calculate average accuracy
    avg_accuracy = stats['total_accuracy'] / stats['accessible'] if stats['accessible'] > 0 else 0

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print("BATCH VERIFICATION COMPLETE")
    print("=" * 80)
    print(f"\nTotal files: {stats['total']}")
    print(f"✓ Accessible pages: {stats['accessible']}")
    print(f"✗ Inaccessible pages: {stats['inaccessible']}")
    print(f"✓ Topic count matches: {stats['topic_matches']}/{stats['accessible']}")
    print(f"\nAccuracy Distribution:")
    print(f"  High (≥80%): {stats['high_accuracy']}")
    print(f"  Medium (50-79%): {stats['medium_accuracy']}")
    print(f"  Low (<50%): {stats['low_accuracy']}")
    print(f"\nAverage accuracy: {avg_accuracy:.1f}%")
    print(f"Time elapsed: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")

    # Save detailed report
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'stats': stats,
        'average_accuracy': round(avg_accuracy, 2),
        'results': [
            {
                'file_name': r.file_name if hasattr(r, 'file_name') else r.get('file_name'),
                'url': r.url if hasattr(r, 'url') else r.get('url', ''),
                'accessible': r.page_accessible if hasattr(r, 'page_accessible') else False,
                'accuracy': r.accuracy_score if hasattr(r, 'accuracy_score') else 0,
                'topic_count_match': r.topic_count_match if hasattr(r, 'topic_count_match') else False,
                'warnings': r.warnings if hasattr(r, 'warnings') else [],
                'errors': r.errors if hasattr(r, 'errors') else r.get('error', [])
            }
            for r in results
        ]
    }

    with open(VERIFICATION_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Detailed report saved: {VERIFICATION_OUTPUT}")

    # Show files with low accuracy
    low_acc_files = [r for r in results if hasattr(r, 'accuracy_score') and r.accuracy_score < 50]
    if low_acc_files:
        print(f"\nFiles with accuracy < 50% ({len(low_acc_files)}):")
        for r in low_acc_files[:10]:  # Show first 10
            print(f"  - {r.file_name}: {r.accuracy_score:.1f}%")

    print("\n✓ Batch verification complete!")


if __name__ == '__main__':
    main()
