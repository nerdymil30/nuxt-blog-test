---
title: "Getting Started with Nuxt Content"
slug: "getting-started-with-nuxt-content"
description: "Learn how to build a markdown-based blog with Nuxt Content module"
publishedAt: "2025-01-15"
author: "Blog Author"
tags: ["nuxt", "content", "markdown", "tutorial"]
image: "/images/blog/nuxt-content-hero.jpg"
draft: false
---

# Getting Started with Nuxt Content

Changed content-check

Welcome to your new markdown-based blog! This post will guide you through the basics of creating content with Nuxt Content.

## What is Nuxt Content?

Nuxt Content is a powerful module that allows you to write content in Markdown, JSON, YAML, or CSV format and consume it in your Nuxt application with a MongoDB-like API.

### Key Features

- **Git-based CMS**: Your content lives in your repository
- **Markdown support**: Write content in markdown with frontmatter
- **Syntax highlighting**: Built-in code highlighting
- **Full-text search**: Search through your content
- **Auto-generated navigation**: Automatically generate navigation from your content structure

## Writing Content

Content files are placed in the `content/` directory. You can organize them in subdirectories and they will be available via the API.

### Frontmatter

Each markdown file starts with frontmatter - YAML metadata between triple dashes:

```yaml
---
title: "Your Post Title"
description: "A brief description"
publishedAt: "2025-01-15"
author: "Author Name"
tags: ["tag1", "tag2"]
---
```

### Markdown Features

You can use all standard markdown features:

- **Bold text**
- *Italic text*
- [Links](https://nuxt.com)
- Lists
- Code blocks
- Images
- Tables

### Code Highlighting

Nuxt Content automatically highlights code blocks:

```javascript
// JavaScript example
const greeting = "Hello, World!";
console.log(greeting);
```

```vue
<!-- Vue component example -->
<template>
  <div class="hello">
    {{ message }}
  </div>
</template>

<script setup>
const message = "Hello from Vue!"
</script>
```

## Querying Content

In your Vue components, you can query content using the `queryContent()` function:

```vue
<script setup>
// Get all blog posts
const { data: posts } = await $fetch('/api/_content/query', {
  query: { 
    where: { _path: { $regex: '^/blog' } },
    sort: { publishedAt: -1 }
  }
})
</script>
```

## What's Next?

Now that you understand the basics, you can:

1. Create more blog posts
2. Customize the styling
3. Add search functionality
4. Create content categories
5. Add social sharing features

Happy blogging! 🚀 