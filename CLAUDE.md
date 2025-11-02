# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Nuxt 3 content management application with blog posts and meeting archives. The application provides a modern platform with server-side rendering, Markdown content support, and dynamic filtering capabilities.

### Tech Stack
- **Framework**: Nuxt 3 with Vue 3 (Composition API)
- **Content Management**: @nuxt/content v3 (Markdown-based)
- **Styling**: TailwindCSS
- **Database**: SQLite (better-sqlite3, currently integrated)
- **TypeScript**: Partial (type support available but not required)
- **Data Migration**: Python scripts for WordPress XML extraction

## Development Commands

```bash
# Install dependencies
npm install

# Start development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Generate static site (SSG)
npm run generate

# Prepare Nuxt auto-generated files and TypeScript
npm run postinstall
```

## Project Architecture

### Core Structure

- **`app.vue`** - Root component with NuxtLayout and NuxtPage setup
- **`nuxt.config.ts`** - Main Nuxt configuration with TailwindCSS and @nuxt/content modules
- **`content.config.ts`** - Content collection configuration (defines blog collection with `**/*.md` pattern)
- **`tsconfig.json`** - Extends `./.nuxt/tsconfig.json` for TypeScript support

### Directory Overview

| Directory | Purpose |
|-----------|---------|
| `pages/` | File-based routing (auto-converted to routes) |
| `components/` | Reusable Vue components |
| `layouts/` | Page layout templates |
| `content/` | Markdown content files organized by collection |
| `content/blog/` | Blog post Markdown files |
| `content/meetings/` | Meeting archive Markdown files (to be generated) |
| `composables/` | Vue composables for reusable logic |
| `utils/` | Utility functions and helpers |
| `assets/css/` | Global CSS (content.css loaded globally) |
| `public/` | Static assets (images, etc.) |
| `public/images/speakers/` | Speaker headshot images (to be copied from migration assets) |
| `scripts/` | Python migration scripts for WordPress data extraction |
| `AAII-Migration-assets/` | WordPress XML exports and migration output |
| `tasks/` | Project task tracking and documentation |

## Key Components

### Pages

**Blog Listing** (`pages/blog/index.vue`)
- Displays all blog posts with search and multi-tag filtering
- Features:
  - Full-text search across title, description, author, and tags
  - Multi-select tag filtering (OR logic - shows posts with ANY selected tag)
  - Active filter badges with individual and bulk clear options
  - Responsive grid layout (2 columns on desktop)
  - Empty state with filtered count
- Uses `queryCollection('content')` API to fetch posts
- Implements client-side refresh on mount if data is empty

**Blog Post Detail** (`pages/blog/[id].vue`)
- Renders individual blog post with full Markdown content
- Features:
  - Post metadata (author, date, tags)
  - Previous/Next post navigation
  - SEO meta tags
  - ContentRenderer for Markdown rendering
- Uses `queryCollection()` and `queryCollectionItemSurroundings()` for data fetching

**Meetings Archive** (`pages/meetings/index.vue` - To Be Created)
- Will display all archived meeting presentations
- Features:
  - Grid layout of meeting cards
  - Meeting date and topics preview
  - Link to individual meeting detail pages
- Uses `queryCollection('content')` API to fetch meetings
- Follows same patterns as blog listing page

**Meeting Detail** (`pages/meetings/[id].vue` - To Be Created)
- Will render individual meeting with full details
- Features:
  - Meeting metadata (date, archive status)
  - Topics with speaker information
  - Speaker bios and headshots
  - Learning outcomes
  - Archive materials (recordings, PDFs)
  - Previous/Next meeting navigation
- Uses `queryCollection()` and `queryCollectionItemSurroundings()` for data fetching

**Other Pages**
- `pages/index.vue` - Homepage
- `pages/About.vue` - About page
- `pages/projects.vue` - Projects listing page

### Layouts

- **`layouts/default.vue`** - Default page layout
- **`layouts/another-layout.vue`** - Alternative layout option

### Components

**`BlogCard.vue`**
- Displays a single blog post in card format
- Shows title, description, author, date, and tags
- Links to individual post page

**`MeetingCard.vue`** (To Be Created)
- Will display a single meeting in card format
- Shows meeting title, date, and first topic preview
- Links to individual meeting detail page
- Similar structure to BlogCard.vue

**`ContentNavigation.vue`**
- Sidebar component showing available tags
- Supports tag selection with event emission
- Updates when selected tags change

**`ProjectList.vue`**
- Lists projects in a grid format

**`menu.vue`**
- Navigation menu component

## Composables & Utilities

### Composables

**`composables/useBlogPost.js`**
- Provides blog post handling utilities:
  - `normalizePost(post)` - Flattens meta fields to top level
  - `normalizePosts(posts)` - Normalizes array of posts
  - `getPostUrl(post)` - Gets post URL (prefers slug over path)
  - `formatDate(dateString)` - Formats dates to US locale

**`composables/useMeetingPost.js`** (To Be Created)
- Will provide meeting post handling utilities:
  - `normalizeMeeting(meeting)` - Flattens meta fields to top level
  - `normalizeMeetings(meetings)` - Normalizes array of meetings
  - `getMeetingUrl(meeting)` - Gets meeting URL (prefers slug over path)
  - `formatMeetingDate(dateString)` - Formats dates in US locale
  - `getTopicNumber(index)` - Formats topic heading (e.g., "TOPIC 1")
- Follows same patterns as `useBlogPost.js` for consistency

**`composables/useImageExists.js`**
- Checks if image files exist without triggering issues
- Server-side: Uses `fs.existsSync()` on public directory
- Client-side: Uses HEAD fetch with caching
- Exports:
  - `checkImageExists(imagePath)` - Async check with caching
  - `useImageExistsCheck(imagePath)` - Reactive image existence checker
- Shares cache via `utils/imageCache`

### Utilities

**`utils/slugs.js`**
- Post URL and slug utilities:
  - `getPostUrl(post)` - Alternative implementation for post URLs
  - `generateSlug(title)` - Convert title to URL-friendly slug
  - `isValidSlug(slug)` - Validate slug format
  - `parsePostId(id)` - Determine if ID is slug or filename

**`utils/imageCache.js`**
- Global image cache management:
  - `imageCache` - Shared Map for caching results
  - `clearImageCache()` - Clear entire cache
  - `getCacheSize()` - Get cache size
  - `setCacheWithExpiry()` / `getCacheWithExpiry()` - Expiring cache utilities

**`utils/meetingHelpers.js`** (To Be Created)
- Meeting-specific helper functions:
  - `truncateDescription(text, maxLines)` - Truncate description with ellipsis
  - `extractFirstTopic(meeting)` - Get first topic for preview
  - `hasArchiveMaterials(meeting)` - Check if materials exist
  - `sortMeetingsByDate(meetings)` - Sort by date descending (newest first)

## Content Management

### Markdown Files Location
- **Blog Posts**: `content/blog/*.md`
- **Meeting Archives**: `content/meetings/*.md` (to be generated from structured JSON)
- **Blog Structure**: `content/pages/` (if used)

### Frontmatter Schema

**Blog Posts** use frontmatter for metadata:
```yaml
---
title: "Post Title"
description: "Brief description"
author: "Author Name"
publishedAt: "2024-01-15"
image: "/images/post-image.png"
tags: ["tag1", "tag2"]
slug: "custom-url-slug"  # Optional, falls back to filename
draft: false  # Optional
---
```

**Meeting Archives** will use frontmatter for metadata:
```yaml
---
metadata:
  title: "April 2024 Skirball/Webinar ARCHIVE"
  link: "https://aaiila.org/april-2024-skirball-webinar-archive/"
  post_id: "16632"
  post_name: "april-2024-skirball-webinar-archive"
  post_date: "2024-11-17 11:15:22"
  category: "Hotel ANGELENO Monthly Meeting Archived"
  creator: "webeditor"
custom_fields:
  - meta_key: "stunnig_headers_bg_img"
    meta_value: "http://aaiila.org/wp-content/uploads/2018/08/slide_skirball-1.jpg"
  - meta_key: "_thumbnail_id"
    meta_value: "12261"
event:
  date: "Saturday, April 20, 2024"
  status: "ARCHIVED"
topics:
  - id: 1
    speakers:
      - name: "Christine Benz"
        title: "Director of Personal Finance for Morningstar"
        bio: "Christine Benz is director of personal finance..."
        photo_id: "12980"
        photo_local_path: "assets/images/christine-benz_12980.jpg"
    presentation:
      title: "5 Must Knows About Retirement Spending"
      description: "One of the most difficult questions..."
      learning_outcomes:
        - "Several factors affect safe withdrawal rates..."
        - "Retirees can exert control over their plans..."
    materials:
      - type: "recording"
        url: "https://youtu.be/WaUWxt2O4Hg"
        label: "Webinar Recording"
---
```

### Querying Content

Use Nuxt Content v3 API:
```javascript
// Fetch all blog posts
const posts = await queryCollection('content')
  .where('path', 'LIKE', '/blog%')
  .all()

// Fetch all meeting archives
const meetings = await queryCollection('content')
  .where('path', 'LIKE', '/meetings%')
  .all()

// Fetch single post
const post = await queryCollection('content')
  .where('path', '=', '/blog/post-name')
  .first()

// Fetch single meeting
const meeting = await queryCollection('content')
  .where('path', '=', '/meetings/meeting-name')
  .first()

// Get surrounding posts
const [prev, next] = await queryCollectionItemSurroundings('content', post.path)
```

## Important Notes

### @nuxt/content v3 Usage
- The codebase uses the v3 `queryCollection()` API, not the deprecated `queryContent()`
- Always filter by path for content types:
  - Blog posts: `.where('path', 'LIKE', '/blog%')`
  - Meeting archives: `.where('path', 'LIKE', '/meetings%')`
- Posts expose metadata via `post.meta` object (author, publishedAt, tags, etc.)
- Meetings expose metadata via `meeting.metadata`, `meeting.event`, `meeting.topics` objects
- Use `post.path` or `meeting.path` for identification and navigation

### Hybrid Rendering Approach
- The application uses a hybrid rendering strategy with forced client-side refresh
- When data is empty on initial load, `refresh()` is called in `onMounted()`
- This handles edge cases with static generation and ensures posts are available

### Styling
- Global CSS is loaded from `assets/css/content.css`
- TailwindCSS is available for all components
- Dark mode support is configured in components (`.dark:` classes)

### Image Handling
- Images should be placed in the `public/` directory
- Use the `useImageExists` composable to verify image availability
- Client-side caching prevents repeated network requests

## WordPress Migration Workflow

This project includes Python scripts to migrate WordPress content to Nuxt-compatible Markdown files.

### Migration Scripts

**`scripts/extract-structured-data-v2.py`**
- Extracts WordPress XML export to structured JSON and XML files
- Parses WordPress Visual Composer shortcodes
- Handles multi-topic same-speaker edge cases (April 2024, March 2022)
- Outputs to `AAII-Migration-assets/output/structured-json/` and `structured-xml/`
- Generated 50 meeting files with full metadata

**`scripts/download-speaker-images.py`**
- Downloads speaker images from live WordPress pages
- Uses requests/BeautifulSoup with proper browser headers
- Implements name-based image URL matching strategies
- Updates structured data with `photo_local_path` fields
- Saves images to `AAII-Migration-assets/output/assets/images/`

**`scripts/batch-download-all-images.py`**
- Batch processor for all speaker image downloads
- Processes all 50 meeting files
- Generates comprehensive download report
- Achieved 100% success rate (100 images downloaded)

**`scripts/generate-markdown-from-json.py`** (To Be Created)
- Will convert structured JSON to Nuxt Markdown files
- Will output to `content/meetings/` directory
- Will copy speaker images to `public/images/speakers/`
- Will update image paths for web serving

### Migration State

**COMPLETED:**
- ✓ 50 meeting files extracted to JSON format
- ✓ 50 meeting files extracted to XML format
- ✓ 100 speaker images downloaded (4.6MB total)
- ✓ All structured data includes photo_local_path fields
- ✓ Multi-topic same-speaker edge cases handled

**PENDING:**
- Generate Nuxt Markdown files from structured JSON
- Copy assets to public/ directories
- Build Vue components for meetings pages

### Migration Assets Location

```
AAII-Migration-assets/
├── output/
│   ├── structured-json/        # 50 JSON files (source of truth)
│   ├── structured-xml/          # 50 XML files (alternative format)
│   └── assets/
│       └── images/              # 100 speaker headshots
├── AAII Los Angeles - Investing*.xml  # Original WordPress export
└── individual-items/            # Individual post XML files
```

## Development Tips

1. **Adding Blog Posts**: Create `.md` files in `content/blog/` with proper frontmatter
2. **Adding Meeting Archives**: Generate from structured JSON using migration script
3. **Updating Queries**: Modify `queryCollection()` calls to filter content appropriately
4. **Component Styling**: Use TailwindCSS classes; scoped styles available with `<style scoped>`
5. **SEO Meta Tags**: Use `useSeoMeta()` in script setup for page-level metadata
6. **Post Navigation**: Use `getPostUrl()` or `getMeetingUrl()` composable methods for consistent linking
7. **Speaker Images**: Reference using `photo_local_path` field from meeting frontmatter
