// Composable to check if image files exist without triggering Vue Router
import { imageCache } from '~/utils/imageCache'

export const useImageExists = () => {
  // Use shared cache from utils module

  const checkImageExists = async (imagePath) => {
    if (!imagePath) return false
    
    // Check cache first
    if (imageCache.value.has(imagePath)) {
      return imageCache.value.get(imagePath)
    }

    let exists = false

    if (import.meta.server) {
      // Server-side: Check if file exists in public directory
      try {
        const fs = await import('fs')
        const path = await import('path')
        
        // Convert URL path to file system path
        const publicPath = path.join(process.cwd(), 'public', imagePath)
        exists = fs.existsSync(publicPath)
      } catch (error) {
        console.warn('Failed to check file existence on server:', error)
        exists = false
      }
    } else {
      // Client-side: Use fetch with HEAD request to avoid Vue Router
      try {
        const response = await fetch(imagePath, {
          method: 'HEAD',
          cache: 'force-cache' // Use cache to avoid repeated requests
        })
        exists = response.ok
      } catch (error) {
        exists = false
      }
    }

    // Cache the result
    imageCache.value.set(imagePath, exists)
    return exists
  }

  const useImageExistsCheck = (imagePath) => {
    const exists = ref(false)
    const loading = ref(true)

    watchEffect(async () => {
      if (!imagePath.value) {
        exists.value = false
        loading.value = false
        return
      }

      loading.value = true
      try {
        exists.value = await checkImageExists(imagePath.value)
      } catch (error) {
        console.warn('Error checking image existence:', error)
        exists.value = false
      } finally {
        loading.value = false
      }
    })

    return {
      exists: readonly(exists),
      loading: readonly(loading)
    }
  }

  return {
    checkImageExists,
    useImageExistsCheck
    // imageCache is now imported from ~/utils/imageCache
  }
} 