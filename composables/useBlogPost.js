// Helper composable to work with blog post data
export const useBlogPost = () => {
  // Normalize a blog post to have flat access to meta fields
  const normalizePost = (post) => {
    if (!post) return null
    
    return {
      ...post,
      // Flatten commonly used meta fields to top level for convenience
      slug: post.meta?.slug || null,
      publishedAt: post.meta?.publishedAt || null,
      author: post.meta?.author || null,
      tags: post.meta?.tags || [],
      image: post.meta?.image || null,
      draft: post.meta?.draft || false,
      // Keep original meta for full access
      meta: post.meta
    }
  }

  // Normalize an array of posts
  const normalizePosts = (posts) => {
    if (!posts) return []
    return posts.map(normalizePost)
  }

  // Get post URL (prefer slug over path)
  const getPostUrl = (post) => {
    const slug = post.slug || post.meta?.slug
    if (slug) {
      return `/blog/${slug}`
    }
    return post.path
  }

  // Format date helper
  const formatDate = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return {
    normalizePost,
    normalizePosts,
    getPostUrl,
    formatDate
  }
} 