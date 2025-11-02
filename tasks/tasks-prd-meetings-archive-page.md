# Tasks: Meetings Archive Page & Detail Pages

## Relevant Files

### Migration Assets (Source Data)
- `AAII-Migration-assets/output/structured-json/*.json` - 50 structured meeting files in JSON format
- `AAII-Migration-assets/output/structured-xml/*.xml` - 50 structured meeting files in XML format
- `AAII-Migration-assets/output/assets/images/` - 100 speaker headshot images (local downloads)
- `AAII-Migration-assets/output/assets/materials/` - 46 PDF/PPT presentation materials (local downloads)
- `scripts/extract-structured-data-v2.py` - Enhanced extraction script with multi-topic same-speaker support
- `scripts/download-speaker-images.py` - Script to download speaker images from live pages
- `scripts/batch-download-all-images.py` - Batch processor for all speaker image downloads
- `scripts/download-materials.py` - Script to download PDF/PPT materials from live pages
- `scripts/batch-download-all-materials.py` - Batch processor for all materials downloads

### Website Components (To Be Created)
- `content/meetings/*.md` - Markdown meeting files to be generated from structured JSON
- `pages/meetings/index.vue` - Meetings archive listing page with responsive grid layout
- `pages/meetings/[id].vue` - Meeting detail page with program information, topics, speakers, archive materials
- `components/MeetingCard.vue` - Reusable meeting card component (similar structure to BlogCard.vue)
- `composables/useMeetingPost.js` - Meeting-specific utilities (normalize posts, format data, get URLs)
- `utils/meetingHelpers.js` - Helper functions for meeting data parsing and processing
- `public/images/meetings/` - Directory for featured meeting images (to be copied from migration assets)
- `public/images/speakers/` - Directory for speaker headshots (to be copied from migration assets)
- `public/documents/materials/` - Directory for PDF/PPT materials (to be copied from migration assets)

### Notes

- The existing `BlogCard.vue` and `pages/blog/index.vue` serve as architectural templates for meeting components
- The `useBlogPost.js` composable pattern will be adapted for `useMeetingPost.js` to maintain consistency
- All migrations follow existing Nuxt Content v3 patterns using `queryCollection()` API
- Asset organization leverages existing image handling with `useImageExists` composable
- Styling uses TailwindCSS matching the existing design system in the project

### Migration State

**COMPLETED:** WordPress XML to Structured Data Extraction
- ✓ 50 meeting files extracted to JSON format (AAII-Migration-assets/output/structured-json/)
- ✓ 50 meeting files extracted to XML format (AAII-Migration-assets/output/structured-xml/)
- ✓ 100 speaker images downloaded (AAII-Migration-assets/output/assets/images/)
- ✓ 46 PDF/PPT materials downloaded (AAII-Migration-assets/output/assets/materials/)
- ✓ All structured data includes photo_local_path fields for speaker images
- ✓ All structured data includes local_path fields for PDF/PPT materials
- ✓ Multi-topic same-speaker edge cases handled (April 2024, March 2022)

**NEXT PHASE:** Generate Nuxt-Compatible Markdown Files & Build Website
- Need to convert structured JSON → Nuxt Content Markdown files
- Need to copy assets to public/ directories
- Need to build Vue components for meetings listing and detail pages

---

## Tasks

### Phase 1: WordPress XML to Structured Data (COMPLETED ✓)

- [x] 1.0 Enhanced WordPress XML Extraction Script
  - [x] 1.1 Create `scripts/extract-structured-data-v2.py` with shortcode parsing
    - Parse WordPress Visual Composer shortcodes
    - Extract meeting metadata, topics, speakers, presentations
    - Handle multi-topic same-speaker edge cases
  - [x] 1.2 Extract all 50 meeting posts to structured JSON
    - Generate JSON files in AAII-Migration-assets/output/structured-json/
    - Include metadata, event info, topics, speakers, materials
  - [x] 1.3 Extract all 50 meeting posts to structured XML
    - Generate XML files in AAII-Migration-assets/output/structured-xml/
    - Mirror JSON structure in XML format
  - [x] 1.4 Download all speaker images
    - Create `scripts/download-speaker-images.py` with web scraping
    - Use requests/BeautifulSoup with proper headers
    - Implement name-based image URL matching
    - Download 100 speaker images to AAII-Migration-assets/output/assets/images/
    - Update structured data with photo_local_path fields
  - [x] 1.5 Batch process all speaker images
    - Create `scripts/batch-download-all-images.py`
    - Process all 50 meeting files
    - Generate download report with success/failure counts
    - Achieved 100% success rate (100 images, 0 failures)
  - [x] 1.6 Download all presentation materials (PDF/PPT)
    - Create `scripts/download-materials.py` with web scraping
    - Use requests with proper headers for PDF/PPT downloads
    - Sanitize filenames for filesystem safety
    - Download 46 PDF/PPT files to AAII-Migration-assets/output/assets/materials/
    - Update structured data with local_path fields for materials
  - [x] 1.7 Batch process all materials
    - Create `scripts/batch-download-all-materials.py`
    - Process all 28 meeting files with PDF/PPT materials
    - Generate download report with success/failure counts
    - Achieved 100% success rate (46 materials, 0 failures, 160 MB total)

### Phase 2: Generate Nuxt Content Markdown Files

- [ ] 2.0 Create Markdown Generation Script
  - [ ] 2.1 Create `scripts/generate-markdown-from-json.py`
    - Read all JSON files from AAII-Migration-assets/output/structured-json/
    - Generate Nuxt-compatible Markdown files with YAML frontmatter
    - Output to `content/meetings/` directory
    - Use post_name from metadata as filename (e.g., `april-2024-skirball-webinar-archive-16632.md`)
  - [ ] 2.2 Define Markdown frontmatter schema
    - Include all metadata fields: title, link, post_id, post_name, post_date, category, creator
    - Include event info: date, status (ARCHIVED)
    - Include topics array with speakers, presentations, materials
    - Include custom_fields for featured images
    - Store photo_local_path for speaker images
    - Store local_path for PDF/PPT materials
  - [ ] 2.3 Convert structured data to Markdown format
    - Convert topics array to clean Markdown sections
    - Format speaker bios with proper line breaks
    - Format learning outcomes as bullet lists
    - Format materials as clickable links
    - Handle missing/optional fields gracefully
  - [ ] 2.4 Copy assets to public directories
    - Create `public/images/speakers/` directory
    - Create `public/documents/materials/` directory
    - Copy all 100 speaker images from AAII-Migration-assets/output/assets/images/
    - Copy all 46 PDF/PPT materials from AAII-Migration-assets/output/assets/materials/
    - Update photo_local_path references to use `/images/speakers/` prefix
    - Update material local_path references to use `/documents/materials/` prefix
    - Verify all image files copied successfully
    - Verify all PDF/PPT files copied successfully
  - [ ] 2.5 Generate migration report
    - Report total Markdown files generated (should be 50)
    - Report asset copy status (100 speaker images, 46 PDF/PPT materials)
    - List any errors or missing data
    - Validate frontmatter structure

### Phase 3: Create Meeting Data Utilities & Composables

- [ ] 3.0 Create Meeting Data Utilities & Composables
  - [ ] 3.1 Create `composables/useMeetingPost.js`
    - Create `normalizeMeeting(meeting)` function to flatten meta fields to top level
    - Create `normalizeMeetings(meetings)` to normalize array of meetings
    - Create `getMeetingUrl(meeting)` to get meeting URL (prefer slug over path)
    - Create `formatMeetingDate(dateString)` to format dates in US locale (e.g., "Saturday, September 20, 2025")
    - Create `getTopicNumber(index)` to format topic heading (e.g., "TOPIC 1")
    - Export all functions for use in components
  - [ ] 3.2 Create `utils/meetingHelpers.js`
    - Create `truncateDescription(text, maxLines)` to truncate description with ellipsis (3-4 lines)
    - Create `extractFirstTopic(meeting)` to get first topic for preview
    - Create `hasArchiveMaterials(meeting)` to check if materials exist
    - Create `sortMeetingsByDate(meetings)` to sort by date descending (newest first)
    - Export all helpers for use in components and pages
  - [ ] 3.3 Ensure composable compatibility
    - Follow same patterns as `useBlogPost.js` for consistency
    - Use same date formatting approach as existing project
    - Maintain naming conventions with existing codebase
    - Test composables can be imported and used in Vue components

### Phase 4: Build Meetings Listing Page

- [ ] 4.0 Build Meetings Listing Page
  - [ ] 4.1 Create `pages/meetings/index.vue` structure
    - Set up template with container and header section
    - Create heading "All Archived Meeting Presentations"
    - Add subheading "Browse all past presentations and associated PDF materials"
    - Set up main content area and grid layout container
  - [ ] 4.2 Implement data fetching with queryCollection()
    - Use `useAsyncData()` hook to fetch meetings
    - Query collection with path filter: `/meetings%`
    - Sort meetings by date descending (newest first)
    - Normalize meetings using `normalizeMeetings()` composable
    - Add refresh() call on mount if data is empty (hybrid rendering pattern)
  - [ ] 4.3 Create responsive grid layout
    - Implement TailwindCSS grid: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
    - Set gap-8 for spacing between cards
    - Ensure responsive: 1 column mobile, 2 columns tablet, 4 columns desktop
  - [ ] 4.4 Display meeting cards
    - Import and use `MeetingCard.vue` component
    - Pass meeting object as prop to each card
    - Show message if no meetings found
    - Verify card count matches expected 50 meetings
  - [ ] 4.5 Add SEO meta tags
    - Use `useSeoMeta()` for page title and description
    - Set og:title and og:description
    - Set twitter:card metadata
    - Example: "All Archived Meeting Presentations - AAIILA"

### Phase 5: Create Meeting Card Component

- [ ] 5.0 Create Meeting Card Component
  - [ ] 5.1 Create `components/MeetingCard.vue` structure
    - Set up article wrapper with base styles
    - Create image container with aspect ratio
    - Create content area with padding
    - Implement "Read more" button section
  - [ ] 5.2 Implement featured image display
    - Display meeting image if exists (from custom_fields._thumbnail_id)
    - Use `useImageExists()` composable to verify image exists before displaying
    - Set aspect ratio (matches WordPress: likely 16:9 or similar)
    - Apply hover scale transform on image (subtle zoom effect)
    - Handle missing images gracefully with placeholder
  - [ ] 5.3 Display card content
    - Show meeting title with hover color change
    - Show event date from frontmatter (event.date)
    - Show first topic description truncated to 3-4 lines with ellipsis
    - Use existing `line-clamp-3` style pattern from BlogCard
    - Ensure text is readable with proper contrast
  - [ ] 5.4 Style card to match WordPress design
    - Light gray background for card content area (`bg-gray-50` or similar)
    - Image spans full card width at top
    - Red "Read more" button (#FF4444 or similar)
    - Consistent padding and spacing with blog cards
    - Add hover effect: subtle shadow increase or opacity change
    - Dark mode support with appropriate color adjustments
  - [ ] 5.5 Add navigation and interactivity
    - Link title to meeting detail page using `getMeetingUrl()`
    - Link "Read more" button to meeting detail page
    - Ensure all links are working and use correct URL format
    - Verify hover states are smooth and intuitive

### Phase 6: Build Meeting Detail Page & Complete Implementation

- [ ] 6.0 Build Meeting Detail Page & Complete Implementation
  - [ ] 6.1 Create `pages/meetings/[id].vue` structure
    - Set up container and layout
    - Create header section at top
    - Create main content area for program information
    - Create sections for each topic/speaker
    - Create navigation section at bottom
  - [ ] 6.2 Implement header section
    - Fetch meeting by ID using `queryCollection()` with path filter
    - Display meeting date in large text (format from event.date field)
    - Show archive status badge with yellow background and text "THIS IS AN ARCHIVED PRESENTATION FROM THE ABOVE DATE"
    - Add horizontal divider line below header
    - Implement back link or breadcrumb to meetings list
  - [ ] 6.3 Implement program information section
    - Display "PROGRAM INFORMATION" heading (gray, all caps)
    - Display meeting title from metadata
    - Render any body content from Markdown file (if exists)
  - [ ] 6.4 Implement topics and speakers section
    - Display each topic with heading using `getTopicNumber()` helper (e.g., "TOPIC 1", "TOPIC 2")
    - For each topic in `topics` array:
      - Display speaker image from photo_local_path (centered, appropriate size - verify with `useImageExists`)
      - Display speaker name in bold
      - Display speaker title/affiliation in smaller text
      - Display speaker bio if available
      - Display presentation title
      - Display presentation description
      - Display key learning outcomes as bulleted list with custom color (teal/green)
    - Implement visual separation between topics
  - [ ] 6.5 Implement archive materials section
    - Display "ARCHIVE MATERIALS" button/section if materials exist
    - Create buttons/links for each material in topic.materials array:
      - Recording links with play icon (type: "recording") - external YouTube links
      - PDF/Slides download links with file icon (type: "slides") - use local_path for downloaded PDFs
    - Use red button color (#FF4444) matching WordPress design
    - Add external link indicators for YouTube recordings
    - Add download attribute for local PDF materials
    - Display material label text
    - Show file size for downloadable materials (optional)
  - [ ] 6.6 Implement previous/next meeting navigation
    - Use `queryCollectionItemSurroundings()` to get surrounding meetings
    - Display "Previous Meeting" link and navigation
    - Display "Next Meeting" link and navigation
    - Handle cases where previous or next meeting doesn't exist
    - Ensure proper sorting (chronological order by event.date)
  - [ ] 6.7 Add SEO meta tags
    - Use `useSeoMeta()` for page title (meeting title + "- AAIILA")
    - Set description from first topic presentation description
    - Set og:title, og:description, og:image (use featured image if available)
    - Set twitter:card metadata
  - [ ] 6.8 Test with multiple meetings
    - Test with 5+ different meeting files
    - Verify all content displays correctly
    - Test responsive design on mobile, tablet, desktop
    - Verify speaker image loading works
    - Test materials links (recordings and PDFs)
    - Verify PDF downloads work from local paths
    - Verify YouTube recording links open in new tabs
    - Check previous/next navigation at boundaries (first and last meeting)
  - [ ] 6.9 Verify design matches WordPress reference
    - Compare listing page layout with provided WordPress screenshot
    - Compare detail page layout with provided WordPress screenshot
    - Verify colors match (red buttons, yellow badge, etc.)
    - Verify typography and spacing matches
    - Verify responsive behavior on all breakpoints
  - [ ] 6.10 Perform final validation and refinement
    - Test all internal links work correctly
    - Verify no broken speaker images
    - Test external materials links (YouTube recordings)
    - Test local PDF material downloads
    - Verify all 46 PDFs are accessible and download correctly
    - Test dark mode support
    - Check performance with 50 meetings
    - Verify no console errors
    - Test navigation flows (listing → detail → next/previous)
    - Final visual comparison with WordPress design
