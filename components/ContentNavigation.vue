<template>
  <nav class="content-nav">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
      Browse Content
    </h3>
    
    <!-- Categories -->
    <div class="mb-6">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 uppercase tracking-wide">
        Categories
      </h4>
      <div class="space-y-1">
        <NuxtLink
          to="/blog"
          class="content-nav-item"
          :class="{ 'active': $route.path === '/blog' }"
        >
          <div class="flex items-center justify-between">
            <span>All Posts</span>
            <span class="text-xs bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded-full">
              {{ totalPosts }}
            </span>
          </div>
        </NuxtLink>
      </div>
    </div>

    <!-- Popular Tags -->
    <div class="mb-6" v-if="popularTags.length">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 uppercase tracking-wide">
        Popular Tags
      </h4>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="tag in popularTags"
          :key="tag.name"
          @click="handleTagClick(tag.name)"
          class="blog-tag transition-all duration-200 cursor-pointer border-2"
          :class="{
            'bg-blue-500 text-white border-blue-500 shadow-md': selectedTags.includes(tag.name),
            'bg-gray-100 dark:bg-gray-700 border-transparent hover:bg-blue-200 dark:hover:bg-blue-800 hover:border-blue-300': !selectedTags.includes(tag.name)
          }"
        >
          {{ tag.name }} ({{ tag.count }})
          <span v-if="selectedTags.includes(tag.name)" class="ml-1 text-xs">✓</span>
        </button>
      </div>
    </div>

    <!-- Recent Posts -->
    <div v-if="recentPosts.length">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 uppercase tracking-wide">
        Recent Posts
      </h4>
      <div class="space-y-3">
        <article 
          v-for="post in recentPosts.slice(0, 5)" 
          :key="post.path"
          class="group"
        >
          <NuxtLink 
            :to="getPostUrl(post)"
            class="block p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <h5 class="text-sm font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-600 transition-colors line-clamp-2 mb-1">
              {{ post.title }}
            </h5>
            <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <span>{{ post.author }}</span>
              <span>•</span>
              <time :datetime="post.publishedAt">
                {{ formatDate(post.publishedAt) }}
              </time>
            </div>
          </NuxtLink>
        </article>
      </div>
    </div>
  </nav>
</template>

<script setup>
const props = defineProps({
  posts: {
    type: Array,
    default: () => []
  },
  selectedTags: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['tag-selected'])

// Handle tag click with debugging
const handleTagClick = (tagName) => {
  console.log('ContentNavigation: Tag clicked:', tagName, 'Current selected:', props.selectedTags)
  emit('tag-selected', tagName)
}

// Helper to get the correct URL for a post (prefer slug over filename)
const getPostUrl = (post) => {
  if (post.slug) {
    return `/blog/${post.slug}`
  }
  return post.path
}

// Compute total posts
const totalPosts = computed(() => props.posts.length)

// Compute popular tags with counts
const popularTags = computed(() => {
  const tagCounts = new Map()
  
  props.posts.forEach(post => {
    if (post.tags) {
      post.tags.forEach(tag => {
        tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1)
      })
    }
  })
  
  return Array.from(tagCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

// Recent posts (already sorted by date)
const recentPosts = computed(() => {
  return props.posts.slice(0, 5)
})

// Format date helper
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 