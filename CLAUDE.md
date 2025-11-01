# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Nuxt 3 blog application with content management using @nuxt/content v3. The application provides a modern blog platform with server-side rendering, Markdown content support, and dynamic filtering capabilities.

### Tech Stack
- **Framework**: Nuxt 3 with Vue 3 (Composition API)
- **Content Management**: @nuxt/content v3 (Markdown-based)
- **Styling**: TailwindCSS
- **Database**: SQLite (better-sqlite3, currently integrated)
- **TypeScript**: Partial (type support available but not required)

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
| `composables/` | Vue composables for reusable logic |
| `utils/` | Utility functions and helpers |
| `assets/css/` | Global CSS (content.css loaded globally) |
| `public/` | Static assets (images, etc.) |

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

## Content Management

### Markdown Files Location
- **Blog Posts**: `content/blog/*.md`
- **Blog Structure**: `content/pages/` (if used)

### Frontmatter Schema
Blog posts use frontmatter for metadata:
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

### Querying Content

Use Nuxt Content v3 API:
```javascript
// Fetch all blog posts
const posts = await queryCollection('content')
  .where('path', 'LIKE', '/blog%')
  .all()

// Fetch single post
const post = await queryCollection('content')
  .where('path', '=', '/blog/post-name')
  .first()

// Get surrounding posts
const [prev, next] = await queryCollectionItemSurroundings('content', post.path)
```

## Important Notes

### @nuxt/content v3 Usage
- The codebase uses the v3 `queryCollection()` API, not the deprecated `queryContent()`
- Always filter by path for blog posts: `.where('path', 'LIKE', '/blog%')`
- Posts expose metadata via `post.meta` object (author, publishedAt, tags, etc.)
- Use `post.path` for post identification and navigation

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

## Development Tips

1. **Adding Blog Posts**: Create `.md` files in `content/blog/` with proper frontmatter
2. **Updating Queries**: Modify `queryCollection()` calls to filter content appropriately
3. **Component Styling**: Use TailwindCSS classes; scoped styles available with `<style scoped>`
4. **SEO Meta Tags**: Use `useSeoMeta()` in script setup for page-level metadata
5. **Post Navigation**: Use `getPostUrl()` composable method for consistent post linking
