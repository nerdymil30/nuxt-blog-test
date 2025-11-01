# PRD: Meetings Archive Page & Detail Pages

## 1. Introduction/Overview

Recreate the WordPress "All Meetings" page (`https://aaiila.org/all-meetings/`) as a Nuxt component that displays archived meeting presentations in a card-based grid layout. Each card represents a meeting/webinar with an image, title, description, and a "Read more" button that links to a detailed meeting page showing full program information, topics, speakers, and archive materials.

**Goal:** Migrate the WordPress meetings archive system to Nuxt using Markdown files for future data and extracted WordPress data for historical records.

---

## 2. Goals

1. Display all meetings/presentations in a responsive grid card layout (matching the WordPress design)
2. Create individual meeting detail pages with comprehensive program information
3. Support both new Markdown-based meeting data and legacy WordPress data
4. Maintain visual consistency with existing Nuxt blog styling and design patterns
5. Enable easy content management for future meetings through Markdown files

---

## 3. User Stories

- **As a visitor**, I want to browse past meeting presentations and their descriptions so I can understand what content is available in the archive.
- **As a visitor**, I want to click on a meeting card to view the full details, including topics, speakers, and downloadable archive materials.
- **As a content manager**, I want to add new meetings by creating Markdown files so I can keep the archive updated without touching code.
- **As a visitor**, I want to see consistent design and branding so the meetings page feels like part of the same website as the blog.

---

## 4. Functional Requirements

### 4.1 Meetings Archive Listing Page (`/meetings` or `/all-meetings`)

1. **Display:** Show all meetings in a responsive grid layout (4 columns on desktop, 2 on tablet, 1 on mobile - matching WordPress screenshot)
2. **Card Content:** Each card must display:
   - Meeting image (featured image)
   - Meeting title (e.g., "October 2025 HOTEL Angeleno /Webinar ARCHIVE")
   - Description text (3-4 lines max, truncated with ellipsis)
   - "Read more" button (red color, matching WordPress design)
3. **Card Styling:**
   - Light gray background for card content area
   - Image spans full card width at top
   - Consistent padding and spacing
   - Hover effect on cards (subtle shadow or opacity change)
4. **Data Source:** Query Markdown files from `content/meetings/` directory using `queryCollection()` API
5. **Sorting:** Display meetings in reverse chronological order (newest first)
6. **No Filtering:** Keep functionality simple - no search, filters, or pagination

### 4.2 Meeting Detail Page (`/meetings/[id]`)

1. **Header Section:**
   - Display meeting date in large text (e.g., "Saturday, September 20, 2025")
   - Show archive status badge (yellow background with text "THIS IS AN ARCHIVED PRESENTATION FROM THE ABOVE DATE")
   - Horizontal divider line

2. **Program Information Section:**
   - "PROGRAM INFORMATION" heading (gray, all caps)
   - Display meeting description and overview

3. **Topics & Speakers Section:**
   - Display each topic with heading (e.g., "TOPIC 1", "TOPIC 2")
   - For each topic:
     - Show speaker image (centered, appropriate size)
     - Speaker name
     - Speaker title/affiliation
     - Topic description
     - Key learning points (if available, displayed as bulleted links with custom color)
   - Buttons for "ARCHIVE MATERIALS" and "WEBINAR RECORDING" (if available)

4. **Related Content:** Display navigation to previous/next meetings (if applicable)

5. **Metadata Display:**
   - Show meeting metadata (author, date, tags if available)
   - Display archive materials section if PDFs or recordings exist

6. **Navigation:**
   - Previous/Next meeting navigation at bottom
   - Breadcrumb or back link to meetings list

### 4.3 Data Structure (Markdown Frontmatter)

Meetings stored as Markdown files in `content/meetings/` should include:

```yaml
---
title: "October 2025 HOTEL Angeleno /Webinar ARCHIVE"
description: "Financial Education meeting information that focuses on the broad overview of basic individual investing in today's market."
date: "2025-10-15"
image: "/images/meetings/hotel-angeleno-oct.png"
archiveStatus: "archived"
topics:
  - title: "Fed independence, Fed Interest Rate Policy, and the Outlook for the Economy"
    speaker: "Lorie Logan"
    speakerTitle: "Chief Market Strategist, The Wealth Consulting Group"
    speakerImage: "/images/speakers/lorie-logan.jpg"
    description: "Come learn about the Fed and how it works from the former President and CEO of the Federal Reserve Bank of Atlanta..."
    keyPoints:
      - "HOW THE FEDERAL OPEN MARKET COMMITTEE (FOMC) MAKES MONETARY POLICY DECISIONS"
      - "WHAT FED INDEPENDENCE IS ABOUT"
      - "WHAT MONETARY POLICY CAN AND CANNOT DO"
  - title: "The Daunting Task of Setting an S+P Target"
    speaker: "Talley Léger"
    speakerTitle: "Chief Market Strategist, The Wealth Consulting Group"
    speakerImage: "/images/speakers/talley-leger.jpg"
    description: "..."
    keyPoints: [...]
archiveMaterials:
  - type: "PDF"
    title: "Meeting Slides"
    url: "/documents/october-2025-slides.pdf"
  - type: "Recording"
    title: "Webinar Recording"
    url: "https://vimeo.com/xxxxx"
slug: "october-2025-hotel-angeleno"
---
```

---

## 5. Non-Goals (Out of Scope)

- **No Search/Filter:** Meeting search, date filters, or category filtering
- **No Pagination:** Display all meetings on one page or use simple "load more" (not required initially)
- **No User Registration:** No sign-up or login required to view meetings
- **No Comments/Discussion:** No comment section on detail pages
- **No Email Notifications:** No subscribe or notification functionality
- **Dynamic Recording Embedding:** Webinar recordings are linked, not embedded inline (keep it simple)

---

## 6. Design Considerations

1. **Design Reference:** Match the WordPress design exactly as shown in the provided screenshots
2. **Color Scheme:**
   - Primary accent: Red buttons (#FF4444 or similar)
   - Headings: Dark blue/navy
   - Status badge: Yellow background
   - Text: Dark gray/black for body, lighter gray for metadata
3. **Typography:**
   - Use existing TailwindCSS and Nuxt styling
   - Bold titles (font-bold or higher weight)
   - Regular body text with 1.5 line height for readability
4. **Layout:**
   - Cards layout: 4 columns desktop (use TailwindCSS grid)
   - Image aspect ratio: Match WordPress (appears to be 16:9 or similar)
   - Card spacing and padding: Consistent with existing blog cards
5. **Responsive Design:**
   - Desktop: 4-column grid
   - Tablet: 2-column grid
   - Mobile: 1-column layout
6. **Component Reuse:** Leverage existing components (e.g., reuse BlogCard structure if applicable)

---

## 7. Technical Considerations

### 7.1 Data Migration Approach (Automated)

**Source:** Complete WordPress XML export (`aaiilaorg.WordPress.2025-07-27 (1).xml`) - 9MB file
**Total Meetings to Migrate:** 24 archived webinar/meeting posts

**Migration Process:**
1. **Python XML Parser Script** (`scripts/migrate-meetings.py`):
   - Parse WordPress XML export using `xml.etree.ElementTree`
   - Extract 24 meeting posts (filter by "ARCHIVE" in title)
   - Parse post content, metadata, and relationships
   - Generate Markdown files with proper frontmatter structure
   - Extract speaker information, topics, and key learning points from HTML content

2. **Asset Organization:**
   - Copy featured meeting images from `AAII-Migration-assets/uploads/` → `public/images/meetings/`
   - Copy speaker headshots → `public/images/speakers/`
   - Copy PDF materials → `public/documents/meetings/`
   - Update image/PDF paths in generated Markdown frontmatter

3. **Output:** 24 Markdown files in `content/meetings/` with complete frontmatter matching schema (section 4.3)

### 7.2 Nuxt Integration

1. **Content API:** Use `queryCollection('content')` with `.where('path', 'LIKE', '/meetings%')` to fetch meetings
2. **Image Handling:** Use existing `useImageExists` composable to verify speaker and meeting images exist
3. **Date Formatting:** Use existing `formatDate()` composable for consistent date display
4. **File Structure:**
   - Create `content/meetings/` directory for Markdown files (auto-created by migration script)
   - Create `pages/meetings/index.vue` for listing page
   - Create `pages/meetings/[id].vue` for detail pages
   - Create `components/MeetingCard.vue` for card component
5. **Slug/ID Handling:** Use existing `getPostUrl()` or create similar utility for meeting URLs
6. **Image Storage:** Featured images and speaker photos stored in `public/images/meetings/` and `public/images/speakers/`

### 7.3 Available Assets

**WordPress Export:**
- `AAII-Migration-assets/aaiilaorg.WordPress.2025-07-27 (1).xml` (9.0 MB)
- Complete post metadata, content, and attachment information

**Images (Already Downloaded):**
- Speaker photos: `uploads/2025/06/` (Dan Niles, Kim Forrest, etc.)
- Featured meeting images: Organized by year/month
- PDF thumbnails: Generated versions available

**Documents:**
- PDF files: Slides, materials in `uploads/2025/` directories
- Organized by meeting date (01-07 folders for 2025)

---

## 8. Success Metrics

1. Meetings listing page displays all meetings in correct grid layout
2. Each meeting card shows image, title, description, and "Read more" button
3. Clicking "Read more" navigates to meeting detail page with all required information
4. Meeting detail pages display topics, speakers, descriptions, key learning points, and archive materials
5. Previous/Next meeting navigation works correctly
6. Design matches WordPress reference screenshots
7. Responsive design works on mobile, tablet, and desktop
8. New meetings can be added by creating Markdown files in `content/meetings/`
9. All internal links work correctly
10. Images display properly (no broken images)

---

## 9. Implementation Steps (Phase 1: MVP)

### Step 1: Build WordPress XML Migration Script
- [ ] Create `scripts/migrate-meetings.py` Python script
- [ ] Parse WordPress XML export file (`aaiilaorg.WordPress.2025-07-27 (1).xml`)
- [ ] Extract all 24 meeting posts (filter by "ARCHIVE" in title)
- [ ] Parse HTML content to extract topics, speakers, and key learning points
- [ ] Generate Markdown files with proper frontmatter structure (matching schema in section 4.3)
- [ ] Create migration report showing:
  - Total posts processed
  - Any parsing errors or missing data
  - File mapping (WordPress post ID → Markdown filename)

### Step 2: Organize and Copy Assets
- [ ] Copy featured meeting images from `AAII-Migration-assets/uploads/` → `public/images/meetings/`
- [ ] Copy speaker headshots → `public/images/speakers/`
- [ ] Copy PDF materials → `public/documents/meetings/`
- [ ] Update image/PDF paths in generated Markdown frontmatter files
- [ ] Verify all image and document files exist and are accessible

### Step 3: Validate Generated Data
- [ ] Verify all 24 Markdown files created in `content/meetings/`
- [ ] Audit frontmatter structure against schema
- [ ] Check for missing or malformed data
- [ ] Validate image paths and PDF links
- [ ] Test parsing of one meeting post with Nuxt

### Step 4: Create Meetings Listing Page
- [ ] Create `pages/meetings/index.vue`
- [ ] Implement queryCollection() to fetch all meetings
- [ ] Create responsive grid layout (4 columns on desktop)
- [ ] Display meeting cards with image, title, description, "Read more" button
- [ ] Implement card styling to match WordPress design

### Step 5: Create Meeting Card Component
- [ ] Create `components/MeetingCard.vue`
- [ ] Reuse existing card styling patterns
- [ ] Implement hover effects
- [ ] Test with multiple meeting variations

### Step 6: Create Meeting Detail Page
- [ ] Create `pages/meetings/[id].vue`
- [ ] Implement header section with date and archive status badge
- [ ] Implement topics/speakers section with images and descriptions
- [ ] Implement key learning points display
- [ ] Implement archive materials section (PDF links, recording links)
- [ ] Add previous/next meeting navigation

### Step 7: Testing & Refinement
- [ ] Test responsive design on all breakpoints
- [ ] Verify all internal links work
- [ ] Test image loading and PDF links
- [ ] Compare design with WordPress reference
- [ ] Test with 5+ different meeting posts to ensure robustness

---

## 10. Open Questions & Decisions

### Answered Questions

1. **Speaker Images:** ✅ **Stored locally** - Copy from WordPress uploads to `public/images/speakers/`
2. **Archive Materials:** ✅ **Stored locally** - PDF files and materials copied to `public/documents/meetings/`
3. **Legacy Data:** ✅ **24 meetings** to migrate from WordPress export
4. **Migration Method:** ✅ **Automated Python script** - Parse WordPress XML and generate Markdown files

### Remaining Decisions

1. **Future Meetings:** Will future meetings be added manually as Markdown files, or via an admin interface/headless CMS?
   - Current plan: Manual Markdown file creation in `content/meetings/`
   - Future enhancement: Could add admin UI if needed

2. **Meeting Status:** Should past/future/upcoming status be indicated differently in the UI?
   - Current plan: All migrated meetings marked as "archived"
   - Future: Could support "upcoming" and "in-progress" statuses if needed

3. **Navigation Structure:** Should there be a main navigation link to /meetings, or should it be accessible via a specific menu?
   - Recommendation: Add to main navigation menu for discoverability
   - Could also add link in blog or resources section

4. **Recording URLs:** Should webinar recordings link to external platforms (Vimeo, YouTube) or be self-hosted?
   - Current: Links to external recording platforms
   - Future: Could self-host if needed

---

## 11. Data Migration Strategy

### Phase 1: Automated XML-to-Markdown Conversion

**Primary Task:** Build Python migration script to convert all 24 WordPress meetings into Markdown files

**Script Location:** `scripts/migrate-meetings.py`

**Input:**
- Source XML: `AAII-Migration-assets/aaiilaorg.WordPress.2025-07-27 (1).xml` (9.0 MB)
- Image Assets: `AAII-Migration-assets/uploads/` (organized by year/month)

**Output:**
- 24 Markdown files in `content/meetings/` with complete frontmatter
- Migration report: `migration-report.md`
- Organized assets in `public/images/` and `public/documents/`

**Estimated Effort:**
- Script development: 2-3 hours
- Asset organization and validation: 1-2 hours
- Total: 3-5 hours (one-time effort)

### Meetings to Migrate

The WordPress export contains 24 archive posts including:
- October 2025 HOTEL Angeleno /Webinar ARCHIVE
- September 2025 Webinar ARCHIVE
- July 2025 Webinar ARCHIVE
- June 2025 Webinar ARCHIVE
- And 20 additional archived webinars from 2023-2025

### Post-Migration

**After Markdown files are generated:**
1. Validate frontmatter structure (sample from section 4.3)
2. Spot-check 3-5 meetings for completeness
3. Verify all images and PDFs are accessible
4. Then proceed with building Nuxt pages (sections 9.4-9.7)

### Future Meetings

New meetings created after migration should be:
- Added manually as Markdown files in `content/meetings/`
- Following the frontmatter structure defined in section 4.3
- No future WordPress synchronization needed
