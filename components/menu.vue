<template>
  <nav class="w-full overflow-x-auto scrollbar-hide menu-scroll">
    <ul class="flex gap-4 py-2 px-1 min-w-max md:min-w-0 md:flex-row md:gap-2 md:py-0 md:px-0">
      <li class="flex-shrink-0">
        <NuxtLink to="/" class="menu-item" active-class="menu-item-active">
          Main
        </NuxtLink>
      </li>
      <li class="flex-shrink-0">
        <NuxtLink to="/about" class="menu-item" active-class="menu-item-active">
          About
        </NuxtLink>
      </li>
      <li class="flex-shrink-0">
        <NuxtLink to="/projects" class="menu-item" active-class="menu-item-active">
          Projects
        </NuxtLink>
      </li>
      <li class="flex-shrink-0">
        <NuxtLink to="/blog" class="menu-item" active-class="menu-item-active">
          Blog
        </NuxtLink>
      </li>
    </ul>
  </nav> 
</template>



<style scoped>
/* Horizontal scroll behavior for mobile */
.menu-scroll {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

/* Hide scrollbar but keep functionality */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Mobile-first menu item styling */
.menu-item {
  @apply flex-shrink-0 px-4 py-2 text-sm font-medium font-mono;
  @apply bg-white dark:bg-gray-800 rounded-full border border-gray-200 dark:border-gray-700;
  @apply text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900;
  @apply whitespace-nowrap transition-all duration-200;
  @apply shadow-sm hover:shadow-md;
  /* Touch targets minimum 44px height */
  min-height: 44px;
  display: flex;
  align-items: center;
}

/* Active state styling */
.menu-item-active {
  @apply bg-blue-500 text-white border-blue-500 shadow-md;
  @apply hover:bg-blue-600 dark:hover:bg-blue-600;
}

/* Medium screens and up: revert to original style */
@media (min-width: 768px) {
  .menu-item {
    @apply p-1 bg-transparent border-transparent shadow-none;
    @apply text-blue-500 hover:bg-green-200 rounded-md;
    @apply min-h-0;
    min-height: auto;
  }
  
  .menu-item-active {
    @apply bg-green-200 text-blue-700 border-transparent shadow-none;
    @apply hover:bg-green-300;
  }
}
</style>

