/**
 * Utility functions for handling blog post slugs
 */

/**
 * Get the correct URL for a blog post
 * Prefers explicit slug from frontmatter, falls back to _path
 * @param {Object} post - The blog post object
 * @returns {string} - The URL path for the post
 */
export function getPostUrl(post) {
  if (post.slug) {
    return `/blog/${post.slug}`
  }
  return post._path
}

/**
 * Generate a URL-friendly slug from a title
 * @param {string} title - The title to convert to a slug
 * @returns {string} - URL-friendly slug
 */
export function generateSlug(title) {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special characters
    .replace(/[\s_-]+/g, '-') // Replace spaces and underscores with dashes
    .replace(/^-+|-+$/g, '') // Remove leading/trailing dashes
}

/**
 * Validate if a slug is URL-friendly
 * @param {string} slug - The slug to validate
 * @returns {boolean} - Whether the slug is valid
 */
export function isValidSlug(slug) {
  const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
  return slugPattern.test(slug)
}

/**
 * Extract post identifier from URL parameter
 * Works with both slugs and filename-based IDs
 * @param {string} id - The URL parameter
 * @returns {Object} - Object with type and value
 */
export function parsePostId(id) {
  // Check if it looks like a generated slug (shorter, cleaner)
  if (isValidSlug(id) && !id.includes('.')) {
    return { type: 'slug', value: id }
  }
  
  // Assume it's a filename-based ID
  return { type: 'filename', value: id }
} 