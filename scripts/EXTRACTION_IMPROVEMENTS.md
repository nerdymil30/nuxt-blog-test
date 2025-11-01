# Extraction Improvements - Test Results and Fixes Needed

## Current Status

Created and tested improved extraction logic on July 2025 Webinar (Post ID: 17614) with excellent results.

### Test Files Created
- **`test-extraction-single.py`** - Initial diagnostic script that identified extraction issues
- **`test-extraction-improved.py`** - Improved script demonstrating correct extraction patterns

## Extraction Issues Found and Fixed

### ✅ Issue 1: Topic Titles Being Extracted as Labels (FIXED)
**Problem:** Original script extracted "TOPIC 1", "TOPIC 2" instead of actual presentation titles

**Root Cause:**
- XML structure has multiple `[dfd_heading]` tags
- Pattern: `[dfd_heading]TOPIC 1[/dfd_heading]` (just a label)
- Followed by: `[dfd_heading]Actual Title Here[/dfd_heading]` (the real title)

**Solution:**
```python
# Extract headings with positions
heading_matches = list(re.finditer(
    r'\[dfd_heading[^\]]*\]([^[]*)\[/dfd_heading\]',
    content,
    re.IGNORECASE | re.DOTALL
))

# Find TOPIC N pattern and pair with next heading
for i, heading_text in enumerate(headings):
    if f"TOPIC {topic_num}" in heading_text.upper():
        if i + 1 < len(headings):
            actual_title = headings[i + 1]
            if "TOPIC" not in actual_title.upper():
                topics.append({'title': actual_title, ...})
```

**Result:**
- ✅ Topic 1: "Dreaming of Sleigh Bells, but Thinking I will Receive Coal"
- ✅ Topic 2: "What the Heck is Happening in the Markets!?!?! -First Principles Investing- using fundamental analysis to calm uncertainty"

### ✅ Issue 2: Duplicate Speakers (FIXED)
**Problem:** Same speaker (Dan Niles) appeared twice in extraction

**Root Cause:** Script wasn't tracking already-extracted speakers

**Solution:**
```python
seen_speakers = set()
speaker_key = (name, title)
if speaker_key not in seen_speakers:
    speakers.append({...})
    seen_speakers.add(speaker_key)
```

**Result:**
- ✅ 2 unique speakers correctly extracted
- ✅ Dan Niles appears once
- ✅ Kim Forrest appears once

### ✅ Issue 3: URLs Not Properly Decoded (FIXED)
**Problem:** Archive material URLs had format `url:https%3A%2F%2F...||target:_blank|`

**Root Cause:**
- URL encoding not decoded
- Trailing format parameters not removed

**Solution:**
```python
# Extract URL from "url:..." format
url_match = re.search(r'url:([^|]*)', button_link)
if url_match:
    url = url_match.group(1).strip()
    url = unquote(url)  # URL decode
    url = html.unescape(url)  # HTML entity unescape
```

**Result:**
- ✅ All 4 archive materials with clean URLs:
  - `https://community.aaii.com/HigherLogic/System/DownloadDocumentFile.ashx?...`
  - `https://aaiila.org/wp-content/uploads/2025/07/DanNiles20250717Final.pdf`
  - etc.

### ✅ Issue 4: Missing Descriptions (FIXED)
**Problem:** Description field was empty in all posts

**Root Cause:**
- WordPress XML `<description>` field is empty
- Actual descriptions are in `[vc_column_text]` blocks

**Solution:**
```python
# Extract from [vc_column_text] blocks
column_matches = re.finditer(
    r'\[vc_column_text[^\]]*\](.*?)\[/vc_column_text\]',
    content,
    re.IGNORECASE | re.DOTALL
)

# Filter for actual descriptions (not headers, sufficient length)
if len(text_no_tags) > 50 and not re.match(r'^(PROGRAM|ARCHIVE|Attend)', text_no_tags):
    descriptions.append(text_no_tags)
```

**Result:**
- ✅ 4 description blocks extracted:
  1. "Dan Niles is the Founder of Niles Investment Management..."
  2. "While I remain somewhat bullish in the near-term..."
  3. "Ms. Forrest founded Bokeh Capital Partners LLC..."
  4. "Market turmoil has been the headline..."

### ✅ Issue 5: Learning Points Not Extracted (FIXED)
**Problem:** Learning points (key takeaways) were empty arrays

**Root Cause:**
- Data stored in URL-encoded JSON within `[dfd_icon_list]` shortcode
- `list_fields="%5B%7B%22icon_type%22%3A..."`

**Solution:**
```python
# Find [dfd_icon_list ...] shortcode
list_fields_match = re.search(r'list_fields="([^"]*)"', attrs)
if list_fields_match:
    list_fields_encoded = list_fields_match.group(1)
    list_fields_decoded = unquote(list_fields_encoded)  # URL decode
    items = json.loads(list_fields_decoded)  # Parse JSON

    # Extract text_content from each item
    for item in items:
        if 'text_content' in item:
            points.append(item['text_content'])
```

**Result:**
- ✅ 6 learning points extracted and parsed:
  1. "Why I was bearish entering the year, got bullish in early April but will get more wary as we approach Thanksgiving"
  2. "Why the economy is probably not as good as it seems due to a pull-forward in demand"
  3. "Where we are in the AI trade"
  4. "How to find your goal and stick to it when managing your portfolio..."
  5. "A refresher on what investors should look at in the financials..."
  6. "How to think about years long trends and position your portfolio..."

## Data Structure Validation

### Tested on Post: July 2025 Webinar ARCHIVE (ID: 17614)

**Metadata Extracted:**
```yaml
title: "July 2025 Webinar ARCHIVE"
date: "2025-06-23 23:57:48"
slug: "17614"
archiveStatus: "archived"
```

**Topics Extracted:** 2
- Topic 1: "Dreaming of Sleigh Bells, but Thinking I will Receive Coal"
- Topic 2: "What the Heck is Happening in the Markets!?!?!..."

**Speakers Extracted:** 2
- Dan Niles (Founder of Dan Niles Investment Management)
- Kim Forrest (Founder & CIO of Bokeh Capital Partners, LLC)

**Learning Points:** 6 (3 per topic)

**Archive Materials:** 4
- 2 Webinar Recordings (with clean URLs)
- 2 Presenter Slides (with clean URLs)

**Descriptions:** 4 blocks
- Speaker biographies
- Talk descriptions
- Key learning objectives

## Integration into migrate-meetings-v3.py

The corrected extraction functions need to be integrated into the main migration script:

### Functions to Update or Add:
1. ✅ `extract_topics_correct()` - Fixed topic title extraction
2. ✅ `extract_speakers_correct()` - Deduplication and proper parsing
3. ✅ `extract_archive_materials_correct()` - URL decoding
4. ✅ `extract_learning_points_correct()` - JSON parsing from URL-encoded data
5. ✅ `extract_speaker_descriptions()` - Extract from column text blocks

### Key Improvements Over v2:
- Topic title pairing logic (label + actual title)
- Speaker deduplication
- URL decoding for archive materials
- JSON parsing for learning points
- Description extraction from column text
- Better HTML entity unescaping

## Next Steps

1. ✅ Test extraction logic (DONE)
2. Create `migrate-meetings-v3.py` with corrected logic
3. Run migration on all 104 posts
4. Validate markdown output
5. Commit to git
