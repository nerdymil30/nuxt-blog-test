<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Header -->
    <header class="text-center mb-12">
      <h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-4">
        Blog
      </h1>
      <p class="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
        Thoughts, tutorials, and insights about web development and technology
      </p>
    </header>

    <div class="flex flex-col lg:flex-row gap-8">
      <!-- Main Content -->
      <main class="flex-1">
        <!-- Search and Filters -->
        <div class="mb-8">
          <div class="flex flex-col md:flex-row gap-4 mb-6">
            <!-- Search -->
            <div class="flex-1">
              <div class="relative">
                <input v-model="searchQuery" type="text" placeholder="🔎 Search blog posts..." 
                class="search-input w-full pl-10" >
              </div>
            </div>
            <!-- Clear All Button -->
            <div v-if="searchQuery || selectedTags.length > 0" class="flex-shrink-0">
              <button 
                @click="clearFilters()"
                class="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
                Clear All
              </button>
            </div>
          </div>

          <!-- Active Filters Display -->
          <div v-if="searchQuery || selectedTags.length > 0" class="flex flex-wrap items-center gap-2 mb-4">
            <span class="text-sm text-gray-500 dark:text-gray-400">Active filters:</span>
            
            <!-- Search Filter Badge -->
            <span v-if="searchQuery" class="inline-flex items-center px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm">
              <span class="mr-2">Search: "{{ searchQuery }}"</span>
              <button @click="searchQuery = ''" class="text-blue-600 dark:text-blue-300 hover:text-blue-800 dark:hover:text-blue-100 ml-1">
                ✕
              </button>
            </span>
            
            <!-- Multiple Tag Filter Badges -->
            <span 
              v-for="tag in selectedTags" 
              :key="tag"
              class="inline-flex items-center px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full text-sm"
            >
              <span class="mr-2">{{ tag }}</span>
              <button @click="removeTag(tag)" class="text-green-600 dark:text-green-300 hover:text-green-800 dark:hover:text-green-100 ml-1" :title="`Remove ${tag} filter`">
                ✕
              </button>
            </span>
            
            <!-- Clear All Tags Button (if multiple tags selected) -->
            <button 
              v-if="selectedTags.length > 1"
              @click="clearTags()"
              class="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 underline"
              title="Clear all tag filters"
            >
              Clear all tags
            </button>
            
            <!-- OR Logic Indicator -->
            <span v-if="selectedTags.length > 1" class="text-xs text-gray-400 dark:text-gray-500 italic">
              (showing posts with any of these tags)
            </span>
            
            <!-- Results Count -->
            <span class="text-sm text-gray-500 dark:text-gray-400">
              ({{ filteredPosts.length }} {{ filteredPosts.length === 1 ? 'post' : 'posts' }} found)
            </span>
          </div>
        </div> 

        <!-- Blog Posts Grid -->
        <div v-if="error" class="text-center py-16">
          <div class="text-6xl mb-4">⚠️</div>
          <h3 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Error loading posts
          </h3>
          <p class="text-gray-600 dark:text-gray-400 mb-6">
            {{ error.message || 'Something went wrong while loading blog posts.' }}
          </p>
        </div>

        <div v-else-if="pending" class="space-y-8">
          <!-- Loading skeleton -->
          <div class="text-center py-8">
            <div class="text-4xl mb-4">📚</div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Loading posts...
            </h3>
            <p class="text-gray-600 dark:text-gray-400">
              Fetching the latest blog content
            </p>
          </div>
          
          <!-- Skeleton cards -->
          <div class="grid gap-8 md:grid-cols-2">
            <div v-for="n in 4" :key="n" class="animate-pulse">
              <div class="bg-gray-200 dark:bg-gray-700 rounded-lg h-48 mb-4"></div>
              <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
              <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
              <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            </div>
          </div>
        </div>

        <div v-else-if="filteredPosts.length === 0" class="text-center py-16">
          <div class="text-6xl mb-4">📝</div>
          <h3 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            No posts found
          </h3>
          <p class="text-gray-600 dark:text-gray-400 mb-6">
            {{ searchQuery ? 'Try adjusting your search.' : 'Blog posts will appear here.' }}
          </p>
          <button
            v-if="searchQuery"
            @click="clearFilters"
            class="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Clear Filters
          </button>
        </div>

        <div v-else class="grid gap-8 md:grid-cols-2">
          <BlogCard
            v-for="post in filteredPosts"
            :key="post.path"
            :post="post"
          />
        </div>
      </main>

      <!-- Sidebar -->
      <aside class="lg:w-80">
        <div class="lg:sticky lg:top-8">
          <ContentNavigation 
            :posts="allPosts || []" 
            :selected-tags="selectedTags"
            @tag-selected="onTagSelected"
          />
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
const { normalizePosts, getPostUrl } = useBlogPost()

// Use lazy loading for better UX - data loads after page renders
const { data: allPosts, pending, error } = await useLazyAsyncData('all-blogPosts', async () => {
  const posts = await queryCollection('content')
    .where('path', 'LIKE', '/blog%')
    .all()
  
  return normalizePosts(posts)
}, {
  default: () => [],
  server: true,    // Try SSR first
  client: true     // Fall back to client if needed
})

console.log('allPosts', allPosts.value)

// Reactive search and filter state
const searchQuery = ref('')
const selectedTags = ref([]) // Multiple tag selection

// Watch selectedTags changes for debugging
watch(selectedTags, (newTags, oldTags) => {
  console.log('selectedTags changed from:', oldTags, 'to:', newTags)
}, { deep: true })

// Compute all available tags
const allTags = computed(() => {
  if (!allPosts.value) return []
  
  const tags = new Set()
  allPosts.value.forEach(post => {
    if (post.tags) {
      post.tags.forEach(tag => tags.add(tag))
    }
  })
  
  return Array.from(tags).sort()
})

// Filter posts based on search and tag
const filteredPosts = computed(() => {
  if (!allPosts.value) return []
  
  let filtered = allPosts.value
  
  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(post => 
      post.title?.toLowerCase().includes(query) ||
      post.description?.toLowerCase().includes(query) ||
      post.author?.toLowerCase().includes(query) ||
      (post.tags && post.tags.some(tag => tag.toLowerCase().includes(query)))
    )
  }
  
  // Filter by selected tags (posts must have ANY of the selected tags - OR logic)
  if (selectedTags.value.length > 0) {
    filtered = filtered.filter(post => 
      post.tags && selectedTags.value.some(tag => post.tags.includes(tag))
    )
  }
  
  return filtered
})

// Clear all filters
const clearFilters = () => {
  searchQuery.value = ''
  selectedTags.value = []
}

// Clear just the tag filters
const clearTags = () => {
  selectedTags.value = []
}

// Clear a specific tag
const removeTag = (tagToRemove) => {
  selectedTags.value = selectedTags.value.filter(tag => tag !== tagToRemove)
}

// Handle tag selection from navigation with toggle behavior
const onTagSelected = (tag) => {
  console.log('Tag clicked:', tag, 'Current selected:', selectedTags.value)
  
  // Toggle behavior - add if not selected, remove if already selected
  if (selectedTags.value.includes(tag)) {
    selectedTags.value = selectedTags.value.filter(t => t !== tag)
    console.log('Tag removed, now selectedTags is:', selectedTags.value)
  } else {
    selectedTags.value = [...selectedTags.value, tag]
    console.log('Tag added, now selectedTags is:', selectedTags.value)
  }
  
  // Scroll to top to show filtered results
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// SEO Meta
useSeoMeta({
  title: 'Blog - Latest Posts and Tutorials',
  description: 'Read the latest blog posts about web development, technology, and programming tutorials.',
  ogTitle: 'Blog - Latest Posts and Tutorials',
  ogDescription: 'Read the latest blog posts about web development, technology, and programming tutorials.',
  twitterTitle: 'Blog - Latest Posts and Tutorials',
  twitterDescription: 'Read the latest blog posts about web development, technology, and programming tutorials.',
  twitterCard: 'summary'
})
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 