// Shared image cache across all components
export const imageCache = ref(new Map())

// Optional: Cache cleanup utilities
export const clearImageCache = () => {
  imageCache.value.clear()
}

export const getCacheSize = () => {
  return imageCache.value.size
}

// Optional: Cache with expiration (future enhancement)
export const setCacheWithExpiry = (key, value, expiryMs = 5 * 60 * 1000) => {
  const expiry = Date.now() + expiryMs
  imageCache.value.set(key, { value, expiry })
}

export const getCacheWithExpiry = (key) => {
  const cached = imageCache.value.get(key)
  if (!cached) return undefined
  
  if (Date.now() > cached.expiry) {
    imageCache.value.delete(key)
    return undefined
  }
  
  return cached.value
} 