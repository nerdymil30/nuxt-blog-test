# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Nuxt 3 blog application with content management using @nuxt/content. The application features:

- **Framework**: Nuxt 3 with Vue 3
- **Content Management**: @nuxt/content for Markdown-based blog posts
- **Styling**: TailwindCSS
- **TypeScript**: Full TypeScript support
- **Database**: SQLite (better-sqlite3)

## Development Commands

```bash
# Install dependencies
npm install

# Start development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Generate static site
npm run generate
```

## Architecture

### Content Management
- **Content Location**: `content/` directory contains Markdown files
- **Blog Posts**: Located in `content/blog/` with `.md` extension
- **Content Config**: `content.config.ts` defines collection structure
- **Content Type**: All content is configured as 'page' type with `**/*.md` source pattern

### Application Structure
- **Entry Point**: `app.vue` - minimal layout wrapper with NuxtLayout and NuxtPage
- **Pages**: File-based routing in `pages/` directory
  - `index.vue` - Homepage
  - `About.vue` - About page
  - `projects.vue` - Projects page
  - `blog/index.vue` - Blog listing page
  - `blog/[id].vue` - Individual blog post page
- **Components**: Reusable components in `components/`
  - `BlogCard.vue` - Blog post card component
  - `ContentNavigation.vue` - Navigation for content
  - `ProjectList.vue` - Project listing component
  - `menu.vue` - Menu component
- **Layouts**: Two layouts available
  - `default.vue` - Default layout
  - `another-layout.vue` - Alternative layout

### Configuration
- **Nuxt Config**: `nuxt.config.ts` configures modules (@nuxtjs/tailwindcss, @nuxt/content)
- **Global CSS**: `assets/css/content.css` loaded globally
- **TypeScript**: Extends Nuxt's generated tsconfig

### Key Features
- File-based routing with dynamic routes for blog posts
- Markdown content processing with @nuxt/content
- TailwindCSS for styling
- TypeScript support throughout
- SQLite database integration