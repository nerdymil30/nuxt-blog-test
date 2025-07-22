#!/usr/bin/env node

/**
 * Utility script to generate slugs for existing blog posts
 * Usage: node scripts/generate-slugs.js
 */

import { readFileSync, writeFileSync, readdirSync } from 'fs'
import { join } from 'path'
import { generateSlug } from '../utils/slugs.js'

const CONTENT_DIR = './content/blog'

function extractFrontmatter(content) {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---/
  const match = content.match(frontmatterRegex)
  
  if (!match) {
    return { frontmatter: '', body: content, hasFrontmatter: false }
  }
  
  return {
    frontmatter: match[1],
    body: content.slice(match[0].length),
    hasFrontmatter: true
  }
}

function parseFrontmatter(frontmatterText) {
  const lines = frontmatterText.split('\n')
  const parsed = {}
  
  for (const line of lines) {
    const colonIndex = line.indexOf(':')
    if (colonIndex > 0) {
      const key = line.slice(0, colonIndex).trim()
      let value = line.slice(colonIndex + 1).trim()
      
      // Remove quotes
      if ((value.startsWith('"') && value.endsWith('"')) || 
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1)
      }
      
      parsed[key] = value
    }
  }
  
  return parsed
}

function updateFrontmatter(frontmatter, newSlug) {
  const lines = frontmatter.split('\n')
  const updatedLines = []
  let slugAdded = false
  
  for (const line of lines) {
    if (line.trim().startsWith('slug:')) {
      // Update existing slug
      updatedLines.push(`slug: "${newSlug}"`)
      slugAdded = true
    } else if (line.trim().startsWith('title:') && !slugAdded) {
      // Add slug after title
      updatedLines.push(line)
      updatedLines.push(`slug: "${newSlug}"`)
      slugAdded = true
    } else {
      updatedLines.push(line)
    }
  }
  
  // If no title found, add slug at the beginning
  if (!slugAdded) {
    updatedLines.unshift(`slug: "${newSlug}"`)
  }
  
  return updatedLines.join('\n')
}

function processFile(filename) {
  const filepath = join(CONTENT_DIR, filename)
  const content = readFileSync(filepath, 'utf-8')
  const { frontmatter, body, hasFrontmatter } = extractFrontmatter(content)
  
  if (!hasFrontmatter) {
    console.log(`⚠️  ${filename}: No frontmatter found, skipping`)
    return
  }
  
  const parsed = parseFrontmatter(frontmatter)
  
  if (parsed.slug) {
    console.log(`✅ ${filename}: Already has slug '${parsed.slug}'`)
    return
  }
  
  if (!parsed.title) {
    console.log(`⚠️  ${filename}: No title found, skipping`)
    return
  }
  
  const newSlug = generateSlug(parsed.title)
  const updatedFrontmatter = updateFrontmatter(frontmatter, newSlug)
  const updatedContent = `---\n${updatedFrontmatter}\n---${body}`
  
  // Write back to file
  writeFileSync(filepath, updatedContent, 'utf-8')
  console.log(`🔧 ${filename}: Generated slug '${newSlug}' from title '${parsed.title}'`)
}

function main() {
  console.log('🚀 Generating slugs for blog posts...\n')
  
  try {
    const files = readdirSync(CONTENT_DIR)
      .filter(file => file.endsWith('.md'))
    
    if (files.length === 0) {
      console.log('No markdown files found in', CONTENT_DIR)
      return
    }
    
    for (const file of files) {
      processFile(file)
    }
    
    console.log(`\n✨ Processed ${files.length} files`)
    console.log('\n💡 Tips:')
    console.log('- Review the generated slugs and adjust manually if needed')
    console.log('- Commit these changes to preserve your URL structure')
    console.log('- Old URLs will still work thanks to the fallback system')
    
  } catch (error) {
    console.error('Error processing files:', error.message)
    process.exit(1)
  }
}

main() 