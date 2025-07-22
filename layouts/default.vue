<template>
    <div class="container mx-auto max-w-4xl">
      <header class="flex flex-col md:flex-row md:justify-between md:items-center gap-3 md:gap-0 pb-3 md:pb-2">
        <!-- Logo/Brand section -->
        <div class="flex justify-between items-center">
          <NuxtLink to="/" class="text-xl font-semibold p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors">
            Ravi Vedula
          </NuxtLink>
        </div>
        
        <!-- Menu section - full width on mobile for scroll -->
        <div class="w-full md:w-auto">
          <Menu />
        </div>
      </header>
      
      <main class="mt-2 p-2">
        <slot />
      </main>
    </div>
</template>

<script setup>
import { useRoute, useHead } from 'nuxt/app'
import { computed } from 'vue'

const route = useRoute()

// Compute fallback title from the last segment of the path
const fallbackTitle = computed(() => {
  // Remove trailing slash if present
  let path = route.path.replace(/\/$/, '')
  // Get last segment
  let last = path.split('/').filter(Boolean).pop() || 'Home'
  // Capitalize and replace dashes/underscores with spaces
  return last
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
})

useHead({
  titleTemplate: '%s -Ravi Vedula',
  title: fallbackTitle,
  link: [
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: 'anonymous' },
    { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Roboto&display=swap' }
  ]
})
</script>

<style>
body {
    font-family: 'Roboto';
        }
        body {
    @apply bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-50;
}
</style>