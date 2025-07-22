

<template>
  <div class="container mx-auto px-4 py-8">
    <div v-if="error" class="text-center py-16">
      <h1 class="text-4xl font-bold text-red-600 mb-4">Post Not Found</h1>
      <p class="text-gray-600 mb-8">The blog post you're looking for doesn't exist.</p>
      <NuxtLink to="/blog" class="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
        Back to Blog
      </NuxtLink>
    </div>

    <article v-else-if="post" class="max-w-4xl mx-auto">
      <!-- Blog Header -->
      <header class="mb-8">
        <h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-4">
          {{ post.title }}
        </h1>
        
        <p class="text-lg text-gray-600 dark:text-gray-400 mb-6">
          {{ post.description }}
        </p>

        <!-- Blog Meta -->
        <div class="blog-meta">
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
            </svg>
            <span>{{ post.author }}</span>
          </div>
          
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd" />
            </svg>
            <time :datetime="post.publishedAt">{{ formatDate(post.publishedAt) }}</time>
          </div>

          <div v-if="post.tags && post.tags.length" class="blog-tags">
            <span 
              v-for="tag in post.tags" 
              :key="tag" 
              class="blog-tag"
            >
              {{ tag }}
            </span>
          </div>
        </div>
      </header>

      <!-- Blog Content using ContentRenderer -->
      <div class="prose prose-lg max-w-none content-renderer-no-title">
        <ContentRenderer :value="post" />
      </div>

      <!-- Navigation -->
      <nav class="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
        <div class="flex justify-between items-center">
          <NuxtLink 
            v-if="prev" 
            :to="getPostUrl(prev)"
            class="group flex items-center gap-2 text-blue-600 hover:text-blue-700 transition-colors"
          >
            <svg class="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            <div>
              <div class="text-sm text-gray-500">Previous</div>
              <div class="font-medium">{{ prev.title }}</div>
            </div>
          </NuxtLink>

          <NuxtLink 
            to="/blog" 
            class="text-gray-600 hover:text-gray-700 transition-colors"
          >
            All Posts
          </NuxtLink>

          <NuxtLink 
            v-if="next" 
            :to="getPostUrl(next)"
            class="group flex items-center gap-2 text-blue-600 hover:text-blue-700 transition-colors text-right"
          >
            <div>
              <div class="text-sm text-gray-500">Next</div>
              <div class="font-medium">{{ next.title }}</div>
            </div>
            <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
            </svg>
          </NuxtLink>
        </div>
      </nav>
    </article>

    <!-- Loading State -->
    <div v-else class="flex justify-center items-center py-16">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  </div>
</template>

<script setup>
const route = useRoute()
const { id } = route.params
console.log('id', id)
const posts = await queryCollection('content').where('path', 'LIKE', '/blog%').all()
console.log('posts', posts)
// Fetch the blog post using correct Nuxt Content v3 queryCollection syntax
const { data: post } = await useAsyncData(`blog-${id}`, async () => {
  try {
    // First, try to find by slug in frontmatter
    const postBySlug = await queryCollection('content')
      .where('path', '=', `/blog/${id}`)
      .first()
    
    if (postBySlug) {
      return postBySlug
    }
    
    // Fallback to path-based lookup for filename matching
    const postByPath = await queryCollection('content')
      .where('path', '=', `/blog/${id}`)
      .first()
    
    return postByPath
  } catch (error) {
    console.error('Error fetching post:', error)
    return null
  }
})

console.log('post', post.value)
console.log('post.value.path', post.value.path)
// Check if post was found
const error = computed(() => !post.value)

// Get surrounding posts for navigation using queryCollectionItemSurroundings
const { data: surroundData } = await useAsyncData(`blog-surround-${id}`, async () => {
  try {
    if (!post.value) return [null, null]
    
    // Use the dedicated surroundings API
    const [prev, next] = await queryCollectionItemSurroundings(
      'content',
      post.value.path,
      {
        fields: ['path', 'title', 'slug']
      }
    )
    console.log('prev', prev)
    console.log('next', next)
    return [prev, next]
  } catch (error) {
    console.error('Error fetching surrounding posts:', error)
    return [null, null]
  }
})
console.log('surroundData', surroundData.value)
const prev = computed(() => surroundData.value?.[0])
const next = computed(() => surroundData.value?.[1])

console.log('slug', post.value.meta.slug)
// Helper to get the correct URL for a post (prefer slug over filename)
const getPostUrl = (post) => {
  if (post.slug) {
    return `/blog/${post.meta.slug}`
  }
  return post.path
}

// Format date helper
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// SEO Meta
watchEffect(() => {
  if (post.value) {
    useSeoMeta({
      title: post.value.title,
      description: post.value.description,
      ogTitle: post.value.title,
      ogDescription: post.value.description,
      ogImage: post.value.image,
      twitterTitle: post.value.title,
      twitterDescription: post.value.description,
      twitterImage: post.value.image,
      twitterCard: 'summary_large_image'
    })
  }
})
</script>