<template>
    <div>
      <h1>About Page</h1>
  
    <button @click="enableLayout">Enable Another Layout</button>
    </div>
  <!-- Responsive container with max-widths -->
  <div >
    <div class="max-w-md ">Small container</div>
    <div class="max-w-4xl mx-auto">Large container</div>
    </div>
  <!-- Grid container -->


<!-- Responsive grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <!-- Items -->
</div>

<div class="grid  grid-rows-10">
  <div class="row-start-3 row-end-10">
    Custom grid area
  </div>
</div>


<div class="bg-white dark:bg-gray-800 rounded-lg px-6 py-8 ring shadow-xl ring-gray-900/5">
    <div>
    <span class="inline-flex items-center justify-center rounded-md bg-indigo-500 p-2 shadow-lg">
      <svg
        class="h-6 w-6 text-white"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <!-- ... -->
      </svg>
    </span>
  </div>
  <h3 class="text-gray-900 dark:text-white mt-5 text-base font-medium tracking-tight ">Writes upside-down</h3>
  <p class="text-gray-500 dark:text-gray-400 mt-2 text-sm ">
    The Zero Gravity Pen can be used to write in any orientation, including upside-down. It even works in outer space.
  </p>
</div>

  </template>


<!-- <script setup>
    
    definePageMeta({
        layout: 'another-layout'
    })
</script> -->

<script setup>
 function enableLayout() {
    setPageLayout('another-layout')
 }
 useHead({
    title: 'About Page',

 })
</script>