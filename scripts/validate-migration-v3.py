#!/usr/bin/env python3
"""
Validate Migration v3 Results
Check generated markdown files for quality and completeness
"""

import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'content' / 'meetings'

class MigrationValidator:
    """Validates migration results"""

    def __init__(self):
        self.stats = {
            'total_files': 0,
            'has_frontmatter': 0,
            'has_title': 0,
            'has_date': 0,
            'has_description': 0,
            'has_speakers': 0,
            'has_topics': 0,
            'has_archive_materials': 0,
            'avg_speakers': 0,
            'avg_topics': 0,
            'avg_materials': 0,
            'total_speakers': 0,
            'total_topics': 0,
            'total_materials': 0,
            'issues': []
        }

    def validate_file(self, file_path):
        """Validate a single markdown file"""
        content = file_path.read_text(encoding='utf-8')

        # Check frontmatter
        if not content.startswith('---'):
            self.stats['issues'].append(f"{file_path.name}: No frontmatter")
            return

        self.stats['has_frontmatter'] += 1

        # Extract frontmatter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            self.stats['issues'].append(f"{file_path.name}: Malformed frontmatter")
            return

        frontmatter = match.group(1)

        # Check fields
        if re.search(r'^title:', frontmatter, re.MULTILINE):
            self.stats['has_title'] += 1

        if re.search(r'^date:', frontmatter, re.MULTILINE):
            self.stats['has_date'] += 1

        if re.search(r'^description:', frontmatter, re.MULTILINE):
            self.stats['has_description'] += 1

        # Count speakers
        speakers = len(re.findall(r'^  - name:', frontmatter, re.MULTILINE))
        if speakers > 0:
            self.stats['has_speakers'] += 1
            self.stats['total_speakers'] += speakers

        # Count topics
        topics = len(re.findall(r'^  - title:', frontmatter, re.MULTILINE))
        if topics > 0:
            self.stats['has_topics'] += 1
            self.stats['total_topics'] += topics

        # Count archive materials
        materials = len(re.findall(r'^  - type:', frontmatter, re.MULTILINE))
        if materials > 0:
            self.stats['has_archive_materials'] += 1
            self.stats['total_materials'] += materials

    def run(self):
        """Run validation"""

        print(f"\n{'='*100}")
        print("MIGRATION v3 VALIDATION REPORT")
        print(f"{'='*100}\n")

        # Find all markdown files
        md_files = sorted(OUTPUT_DIR.glob('*.md'))
        self.stats['total_files'] = len(md_files)

        print(f"Validating {len(md_files)} markdown files...\n")

        # Validate each file
        for file_path in md_files:
            self.validate_file(file_path)

        # Calculate averages
        if self.stats['has_speakers'] > 0:
            self.stats['avg_speakers'] = self.stats['total_speakers'] / self.stats['has_speakers']

        if self.stats['has_topics'] > 0:
            self.stats['avg_topics'] = self.stats['total_topics'] / self.stats['has_topics']

        if self.stats['has_archive_materials'] > 0:
            self.stats['avg_materials'] = self.stats['total_materials'] / self.stats['has_archive_materials']

        # Report
        print(f"{'='*100}")
        print("VALIDATION RESULTS")
        print(f"{'='*100}\n")

        print(f"Total files validated:           {self.stats['total_files']}")
        print(f"\nFrontmatter Quality:")
        print(f"  Has frontmatter:               {self.stats['has_frontmatter']:3d} ({100*self.stats['has_frontmatter']//self.stats['total_files']:3d}%)")
        print(f"  Has title:                     {self.stats['has_title']:3d} ({100*self.stats['has_title']//self.stats['total_files']:3d}%)")
        print(f"  Has date:                      {self.stats['has_date']:3d} ({100*self.stats['has_date']//self.stats['total_files']:3d}%)")
        print(f"  Has description:               {self.stats['has_description']:3d} ({100*self.stats['has_description']//self.stats['total_files']:3d}%)")

        print(f"\nContent Quality:")
        print(f"  Files with speakers:           {self.stats['has_speakers']:3d} ({100*self.stats['has_speakers']//self.stats['total_files']:3d}%)")
        print(f"  Files with topics:             {self.stats['has_topics']:3d} ({100*self.stats['has_topics']//self.stats['total_files']:3d}%)")
        print(f"  Files with archive materials:  {self.stats['has_archive_materials']:3d} ({100*self.stats['has_archive_materials']//self.stats['total_files']:3d}%)")

        print(f"\nData Aggregates:")
        print(f"  Total speakers:                {self.stats['total_speakers']:3d} (avg: {self.stats['avg_speakers']:.1f} per file with speakers)")
        print(f"  Total topics:                  {self.stats['total_topics']:3d} (avg: {self.stats['avg_topics']:.1f} per file with topics)")
        print(f"  Total archive materials:       {self.stats['total_materials']:3d} (avg: {self.stats['avg_materials']:.1f} per file with materials)")

        if self.stats['issues']:
            print(f"\n{'='*100}")
            print(f"ISSUES FOUND ({len(self.stats['issues'])})")
            print(f"{'='*100}\n")
            for issue in self.stats['issues'][:10]:
                print(f"  ⚠️  {issue}")
            if len(self.stats['issues']) > 10:
                print(f"  ... and {len(self.stats['issues']) - 10} more issues")
        else:
            print(f"\n✅ No validation issues found!")

        print(f"\n{'='*100}\n")

def main():
    """Entry point"""
    validator = MigrationValidator()
    validator.run()

if __name__ == '__main__':
    main()
