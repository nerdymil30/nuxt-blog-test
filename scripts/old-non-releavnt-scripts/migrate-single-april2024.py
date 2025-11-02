#!/usr/bin/env python3
"""
Quick script to migrate just April 2024 meeting
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the fixed migrator - use hyphen not underscore
import importlib.util
migrate_script = Path(__file__).parent / 'migrate-meetings-v3.py'
spec = importlib.util.spec_from_file_location("migrate_meetings_v3", migrate_script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
MeetingMigrator = module.MeetingMigrator

def main():
    """Migrate April 2024 file only"""
    migrator = MeetingMigrator()
    migrator.setup_directories()

    # Path to April 2024 XML file
    xml_file = Path(__file__).parent.parent / 'AAII-Migration-assets' / 'individual-posts' / 'monthly-meetings' / 'april-2024-skirballwebinar-archive-16632.xml'

    if not xml_file.exists():
        print(f"ERROR: File not found: {xml_file}")
        return

    print("="*80)
    print("Migrating April 2024 meeting...")
    print("="*80)

    success = migrator.migrate_post(xml_file)

    if success:
        print("\n✓ Successfully migrated April 2024!")
        print(f"\nOutput: content/meetings/")
    else:
        print("\n✗ Migration failed!")

if __name__ == '__main__':
    main()
