<template>
  <article class="blog-card bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow group">
    <!-- Featured Image - only show if image exists -->
    <div v-if="post.image && imageExists" class="aspect-video overflow-hidden">
      <img 
        :src="post.image" 
        :alt="post.title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
      >
    </div>

    <!-- Content -->
    <div class="p-6">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3 group-hover:text-blue-600 transition-colors">
        <NuxtLink :to="getPostUrl(post)" class="hover:underline">
          {{ post.title }}
        </NuxtLink>
      </h2>
      
      <p class="text-gray-600 dark:text-gray-400 mb-4 line-clamp-3">
        {{ post.description }}
      </p>

      <!-- Post Meta -->
      <div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
          </svg>
          <span>{{ post.author }}</span>
        </div>
        
        <time :datetime="post.publishedAt">
          {{ formatDate(post.publishedAt) }}
        </time>
      </div>

      <!-- Tags -->
      <div v-if="post.tags && post.tags.length" class="mb-4">
        <div class="flex flex-wrap gap-2">
          <span 
            v-for="tag in post.tags.slice(0, 3)" 
            :key="tag" 
            class="blog-tag"
          >
            {{ tag }}
          </span>
          <span v-if="post.tags.length > 3" class="text-xs text-gray-500">
            +{{ post.tags.length - 3 }} more
          </span>
        </div>
      </div>

      <!-- Read More -->
      <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
        <NuxtLink 
          :to="getPostUrl(post)"
          class="inline-flex items-center text-blue-600 hover:text-blue-700 transition-colors group"
        >
          Read more
          <svg class="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
          </svg>
        </NuxtLink>
      </div>
    </div>
  </article>
</template>

<script setup>
const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

// Check if image exists using the composable with shared cache
const { useImageExistsCheck } = useImageExists()
const imagePath = computed(() => props.post.image)
const { exists: imageExists, loading: imageLoading } = useImageExistsCheck(imagePath)


// Helper to get the correct URL for a post (prefer slug over filename)
const getPostUrl = (post) => {
  if (post.slug) {
    return `/blog/${post.slug}`
  }
  return post.path
}

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
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 