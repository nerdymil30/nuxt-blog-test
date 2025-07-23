// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },
  nitro: {  
    preset: 'static',
  },
  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxt/content',
  ],

  // Global CSS
  css: ['~/assets/css/content.css']
})