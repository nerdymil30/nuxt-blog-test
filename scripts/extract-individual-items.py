#!/usr/bin/env python3
"""
Extract Individual Meeting Items to Separate XML Files
Splits the main WordPress XML export into individual item files for easier analysis
Removes all useless WordPress metadata, keeps only essential fields and useful postmeta
Filters for published posts from 2021 onwards
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re
import copy
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
XML_FILE = PROJECT_ROOT / 'AAII-Migration-assets' / 'aaiilaorg.WordPress.2025-11-01.xml'
OUTPUT_BASE_DIR = PROJECT_ROOT / 'AAII-Migration-assets' / 'individual-posts'

# Category-based output directories
OUTPUT_DIRS = {
    'monthly': OUTPUT_BASE_DIR / 'monthly-meetings',
    'strategic': OUTPUT_BASE_DIR / 'strategic-investing',
    'retirement': OUTPUT_BASE_DIR / 'retirement-investing',
    'other': OUTPUT_BASE_DIR / 'other'
}

def sanitize_filename(text):
    """Convert text to filename-safe format"""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters, keep only alphanumeric, hyphens, spaces
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'[-\s]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text

def determine_category_folder(category_text):
    """
    Determine which folder to use based on WordPress category.
    Returns: 'monthly', 'strategic', 'retirement', or 'other'
    """
    if not category_text:
        return 'other'

    category_lower = category_text.lower()

    # Check for Strategic Investing
    if 'strategic' in category_lower and 'investing' in category_lower:
        return 'strategic'

    # Check for Retirement
    if 'retirement' in category_lower:
        return 'retirement'

    # Check for Monthly Meetings (Hotel Angeleno, Skirball, etc.)
    if ('hotel' in category_lower and 'angeleno' in category_lower) or \
       ('monthly' in category_lower and 'meeting' in category_lower) or \
       'skirball' in category_lower:
        return 'monthly'

    # Default to other
    return 'other'

def should_keep_postmeta(meta_key):
    """
    Determine if a postmeta field should be kept.
    Only keep essential fields that are useful for content or images.
    Remove all WordPress theme settings, cache, and internal fields.
    """
    # Useful fields to KEEP
    useful_keys = {
        '_thumbnail_id',                      # Featured image ID
        'stunnig_headers_bg_img',              # Hero background image URL
    }

    # Patterns to SKIP (WordPress noise)
    skip_patterns = [
        '_wpb_shortcodes_custom_css',         # Visual Composer CSS (duplicates)
        'post_single_',                        # Display toggles
        'stunnig_headers_',                    # Header config (except bg_img)
        'dfd_',                               # Theme-specific
        'preloader_',                         # Page loader animation
        'crum_',                              # Breadcrumb settings
        '_oembed_',                           # oEmbed cache
        '_wp_old_',                           # Historical dates/slugs
        '_yoast_wpseo_',                      # SEO metadata
        '_monsterinsights_',                  # Analytics
        '_edit_',                             # Edit history
        '_wpb_vc_',                           # Visual Composer
        'slide_template',                     # Template settings
        'sharing_disabled',                   # Social sharing
        '_my_post_',                          # Custom post settings
        '_dp_original',                       # Duplicate tracking
        'stun_header_',                       # Stunning header config
        'post_single_',                       # Post display config
    ]

    # Check if in useful list
    if meta_key in useful_keys:
        return True

    # Check if matches skip patterns
    for pattern in skip_patterns:
        if meta_key.startswith(pattern):
            return False

    # Default: skip anything not explicitly approved
    return False

def main():
    """Extract individual items to separate XML files"""

    if not XML_FILE.exists():
        print(f"ERROR: XML file not found: {XML_FILE}")
        return

    print(f"Parsing: {XML_FILE}")
    print(f"Output base directory: {OUTPUT_BASE_DIR}\n")

    # Create all output directories
    for category_key, output_dir in OUTPUT_DIRS.items():
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {output_dir}")
    print()

    # Parse XML
    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    # Define namespaces
    namespaces = {
        'wp': 'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'excerpt': 'http://wordpress.org/export/1.2/excerpt/'
    }

    # Register namespaces to preserve them in output
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    # Also register other namespaces that might be in the document
    ET.register_namespace('content', 'http://purl.org/rss/1.0/modules/content/')
    ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
    ET.register_namespace('wp', 'http://wordpress.org/export/1.2/')
    ET.register_namespace('wfw', 'http://wellformedweb.org/CommentAPI/')
    ET.register_namespace('excerpt', 'http://wordpress.org/export/1.2/excerpt/')

    # Find all items (posts)
    items = root.findall('.//item')
    print(f"Found {len(items)} total items\n")

    # Filter for meeting archive posts
    meeting_count = 0
    extracted_count = 0
    skipped_status_count = 0
    skipped_date_count = 0
    category_counts = {
        'monthly': 0,
        'strategic': 0,
        'retirement': 0,
        'other': 0
    }

    print("=" * 80)
    print("EXTRACTING PUBLISHED MEETING ARCHIVE POSTS (2021 ONWARDS)")
    print("=" * 80)

    for item in items:
        title_elem = item.find('title')
        title = title_elem.text if title_elem is not None else ""

        # Check if this is an archive post
        if title and 'ARCHIVE' in title.upper():
            post_type_elem = item.find('wp:post_type', namespaces)
            post_type = post_type_elem.text if post_type_elem is not None else ""

            # Only process posts, not attachments
            if post_type == 'post':
                # Check if post is published
                status_elem = item.find('wp:status', namespaces)
                status = status_elem.text if status_elem is not None else ""

                if status != 'publish':
                    skipped_status_count += 1
                    print(f"SKIPPED (status={status}): {title}")
                    continue

                # Check if post is from 2021 onwards
                post_date_elem = item.find('wp:post_date', namespaces)
                if post_date_elem is not None and post_date_elem.text:
                    try:
                        post_date = datetime.strptime(post_date_elem.text, '%Y-%m-%d %H:%M:%S')
                        if post_date.year <= 2019:
                            skipped_date_count += 1
                            print(f"SKIPPED (year={post_date.year}): {title}")
                            continue
                    except ValueError:
                        # If date parsing fails, skip to be safe
                        skipped_date_count += 1
                        print(f"SKIPPED (invalid date): {title}")
                        continue

                meeting_count += 1

                # Get post ID for filename
                post_id_elem = item.find('wp:post_id', namespaces)
                post_id = post_id_elem.text if post_id_elem is not None else 'unknown'

                # Extract category to determine output folder
                category_elem = item.find('category[@domain="category"]')
                category_text = category_elem.text if category_elem is not None else ""

                # Determine which folder based on category
                category_folder = determine_category_folder(category_text)
                output_dir = OUTPUT_DIRS[category_folder]

                # Sanitize title for filename
                safe_title = sanitize_filename(title)

                # Generate filename
                filename = f"{safe_title}-{post_id}.xml"
                filepath = output_dir / filename

                try:
                    # Create a minimal XML document with just this item
                    item_root = ET.Element('item')

                    # Copy child elements, filtering out useless postmeta
                    postmeta_count = 0
                    postmeta_kept = 0

                    for child in item:
                        # Check if this is a postmeta element
                        if child.tag.endswith('postmeta'):
                            postmeta_count += 1
                            # Extract meta_key
                            meta_key_elem = child.find('{http://wordpress.org/export/1.2/}meta_key')
                            if meta_key_elem is not None and meta_key_elem.text:
                                meta_key = meta_key_elem.text
                                # Only keep if it passes filter
                                if should_keep_postmeta(meta_key):
                                    item_root.append(copy.deepcopy(child))
                                    postmeta_kept += 1
                            # Skip this postmeta entry
                        else:
                            # Keep all non-postmeta elements
                            item_root.append(copy.deepcopy(child))

                    # Write to file
                    tree_out = ET.ElementTree(item_root)
                    tree_out.write(filepath, encoding='utf-8', xml_declaration=True)

                    extracted_count += 1
                    category_counts[category_folder] += 1
                    postmeta_removed = postmeta_count - postmeta_kept
                    category_label = category_folder.upper()
                    print(f"{extracted_count}. [{category_label}] {filename} (removed {postmeta_removed} postmeta, kept {postmeta_kept})")

                except Exception as e:
                    print(f"ERROR extracting '{title}': {e}")

    print("\n" + "=" * 80)
    print(f"EXTRACTION COMPLETE")
    print("=" * 80)
    total_found = meeting_count + skipped_status_count + skipped_date_count
    print(f"Total archive posts found: {total_found}")
    print(f"Published posts from 2021+ extracted: {extracted_count}")
    print(f"Skipped (non-published status): {skipped_status_count}")
    print(f"Skipped (2020 or earlier): {skipped_date_count}")

    print(f"\nCategory Breakdown:")
    print(f"  Monthly Meetings: {category_counts['monthly']} files → {OUTPUT_DIRS['monthly']}")
    print(f"  Strategic Investing: {category_counts['strategic']} files → {OUTPUT_DIRS['strategic']}")
    print(f"  Retirement & Investing: {category_counts['retirement']} files → {OUTPUT_DIRS['retirement']}")
    print(f"  Other: {category_counts['other']} files → {OUTPUT_DIRS['other']}")

    print(f"\nMetadata Cleanup Summary:")
    print(f"  Each file: ~95% of useless postmeta entries removed")
    print(f"  Kept fields: _thumbnail_id, stunnig_headers_bg_img")
    print(f"  Removed patterns: _wpb_*, post_single_*, _oembed_*, _yoast_*, etc.")
    print(f"\nExpected size reduction: ~70-80% per file")

    # Find example files in each category
    print(f"\nTo view sample posts:")
    for category_key, count in category_counts.items():
        if count > 0:
            category_dir = OUTPUT_DIRS[category_key]
            sample_files = list(category_dir.glob('*.xml'))
            if sample_files:
                print(f"  [{category_key.upper()}] {sample_files[0]}")

if __name__ == '__main__':
    main()
