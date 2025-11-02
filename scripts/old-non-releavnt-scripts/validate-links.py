#!/usr/bin/env python3
"""
Link Validation Script
Validates all extracted URLs from the consolidated JSON file
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import time

PROJECT_ROOT = Path(__file__).parent.parent
CONSOLIDATED_JSON = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'all-meetings-consolidated.json'
VALIDATION_REPORT = PROJECT_ROOT / 'AAII-Migration-assets' / 'output' / 'validation-report.json'

class LinkValidator:
    def __init__(self):
        self.results = {
            'total_links': 0,
            'active': [],
            'redirects': [],
            'broken': [],
            'timeout': [],
            'by_domain': defaultdict(list)
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def validate_url(self, url: str) -> Tuple[str, int, str]:
        """
        Validate a single URL
        Returns: (status, status_code, final_url or error_message)
        """
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10)
            status_code = response.status_code

            if 200 <= status_code < 300:
                return ('active', status_code, url)
            elif 300 <= status_code < 400:
                return ('redirect', status_code, response.url)
            else:
                return ('broken', status_code, f'HTTP {status_code}')

        except requests.Timeout:
            return ('timeout', 0, 'Request timeout')
        except requests.RequestException as e:
            return ('error', 0, str(e))

    def extract_all_links(self, meetings_data: dict) -> List[Tuple[str, str, str]]:
        """
        Extract all links from meetings data
        Returns list of (url, post_id, context)
        """
        links = []
        for meeting in meetings_data.get('meetings', []):
            post_id = meeting['metadata']['post_id']
            post_name = meeting['metadata']['post_name']

            for topic in meeting.get('topics', []):
                for material in topic.get('materials', []):
                    url = material.get('url', '')
                    if url:
                        material_type = material.get('type', 'unknown')
                        context = f"{post_name} - Topic {topic['id']} - {material_type}"
                        links.append((url, post_id, context))

        return links

    def validate_all(self, links: List[Tuple[str, str, str]]):
        """Validate all links with progress tracking"""
        self.results['total_links'] = len(links)

        print(f"Validating {len(links)} links...")
        print("=" * 80)

        for i, (url, post_id, context) in enumerate(links, 1):
            print(f"{i}/{len(links)}: {url[:60]}...")

            status, status_code, info = self.validate_url(url)

            link_info = {
                'url': url,
                'post_id': post_id,
                'context': context,
                'status_code': status_code,
                'info': info
            }

            # Categorize by status
            if status == 'active':
                self.results['active'].append(link_info)
            elif status == 'redirect':
                link_info['final_url'] = info
                self.results['redirects'].append(link_info)
            elif status == 'broken':
                self.results['broken'].append(link_info)
            elif status == 'timeout' or status == 'error':
                self.results['timeout'].append(link_info)

            # Categorize by domain
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                self.results['by_domain'][domain].append({
                    'url': url,
                    'status': status,
                    'status_code': status_code
                })
            except:
                pass

            # Rate limiting
            time.sleep(0.5)

        print("\n" + "=" * 80)

    def generate_report(self):
        """Generate validation report"""
        total = self.results['total_links']
        active_count = len(self.results['active'])
        redirect_count = len(self.results['redirects'])
        broken_count = len(self.results['broken'])
        timeout_count = len(self.results['timeout'])

        print("LINK VALIDATION RESULTS")
        print("=" * 80)
        print(f"Total links found: {total}")
        print(f"Active/working: {active_count} ({active_count/total*100:.1f}%)")
        print(f"Redirects: {redirect_count} ({redirect_count/total*100:.1f}%)")
        print(f"Broken: {broken_count} ({broken_count/total*100:.1f}%)")
        print(f"Timeout/Error: {timeout_count} ({timeout_count/total*100:.1f}%)")

        print(f"\nBy domain:")
        for domain, links in sorted(self.results['by_domain'].items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {domain}: {len(links)} links")

        if self.results['broken']:
            print(f"\nBroken links ({len(self.results['broken'])}):")
            for link in self.results['broken'][:10]:  # Show first 10
                print(f"  - {link['url']}")
                print(f"    Context: {link['context']}")
                print(f"    Error: {link['info']}")

    def save_report(self):
        """Save validation report to JSON"""
        # Calculate summary
        total = self.results['total_links']
        summary = {
            'total_links': total,
            'active': len(self.results['active']),
            'redirects': len(self.results['redirects']),
            'broken': len(self.results['broken']),
            'timeout': len(self.results['timeout']),
            'active_percentage': round(len(self.results['active'])/total*100, 1) if total > 0 else 0,
            'domains': {domain: len(links) for domain, links in self.results['by_domain'].items()}
        }

        report = {
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': summary,
            'details': {
                'active_links': self.results['active'],
                'redirects': self.results['redirects'],
                'broken_links': self.results['broken'],
                'timeout_links': self.results['timeout']
            }
        }

        with open(VALIDATION_REPORT, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nValidation report saved to: {VALIDATION_REPORT}")

def main():
    """Main execution"""
    print("=" * 80)
    print("LINK VALIDATION")
    print("=" * 80)
    print()

    # Load consolidated JSON
    if not CONSOLIDATED_JSON.exists():
        print(f"ERROR: Consolidated JSON not found at {CONSOLIDATED_JSON}")
        return

    with open(CONSOLIDATED_JSON, 'r', encoding='utf-8') as f:
        meetings_data = json.load(f)

    # Extract and validate links
    validator = LinkValidator()
    links = validator.extract_all_links(meetings_data)

    print(f"Found {len(links)} links to validate\n")

    # Validate all links
    validator.validate_all(links)

    # Generate and save report
    validator.generate_report()
    validator.save_report()

    print("\n✓ Link validation complete!")

if __name__ == '__main__':
    main()
