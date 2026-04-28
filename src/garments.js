/**
 * GARMENT LIBRARY — fully automatic
 * ───────────────────────────────────
 * Drop any PNG into /public/garments/ and it appears in the app.
 * Claude Vision analyzes each image once and caches the result.
 * No manual entries needed anywhere.
 */

const CACHE_VERSION = 'v1'  // bump to force re-analysis of all garments
const ANTHROPIC_KEY = import.meta.env.VITE_ANTHROPIC_API_KEY

// Vite discovers every PNG at build time
const imageModules = import.meta.glob('/public/garments/*.png', { eager: true })

// ─── Analyze a single garment image with Claude Vision ──────────────────────
async function analyzeGarment(imagePath) {
  const cacheKey = `${CACHE_VERSION}:garment:${imagePath}`

  // Return cached result — Claude only runs once per garment ever
  const cached = localStorage.getItem(cacheKey)
  if (cached) {
    try { return JSON.parse(cached) } catch {}
  }

  // Fetch the image and convert to base64 for the API
  const res    = await fetch(imagePath)
  const blob   = await res.blob()
  const base64 = await new Promise((resolve, reject) => {
    const reader   = new FileReader()
    reader.onload  = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': ANTHROPIC_KEY,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 200,
      system: `You are a fashion metadata extractor.
Given a garment image respond ONLY with a valid JSON object — no markdown, no backticks, no explanation.
Required keys:
  label  — short product name e.g. "Slim Fit Jeans" or "Denim Jacket"
  sub    — fabric and color e.g. "Denim · Washed Indigo" or "Cotton · Heather Grey"
  type   — exactly "upper" or "lower" (upper = tops/jackets/hoodies, lower = pants/jeans/skirts)
  tags   — array of exactly 3 lowercase style tags e.g. ["casual","denim","relaxed"]`,
      messages: [{
        role: 'user',
        content: [
          {
            type: 'image',
            source: { type: 'base64', media_type: 'image/png', data: base64 },
          },
          {
            type: 'text',
            text: 'Analyze this garment and return the JSON metadata.',
          },
        ],
      }],
    }),
  })

  if (!response.ok) throw new Error(`Claude API error: ${response.status}`)

  const data = await response.json()
  const meta = JSON.parse(data.content[0].text.trim())

  // Cache so this never runs again for the same garment
  localStorage.setItem(cacheKey, JSON.stringify(meta))
  return meta
}

// ─── Fallback when Claude is unavailable ────────────────────────────────────
function fallbackMeta(id) {
  const label = id.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  const lowerKeywords = ['jean', 'pant', 'trouser', 'skirt', 'short', 'chino', 'legging', 'jogger']
  const type = lowerKeywords.some(k => id.includes(k)) ? 'lower' : 'upper'
  return { label, sub: '', type, tags: [] }
}

// ─── Main loader — returns { all, upper, lower } ─────────────────────────────
export async function loadGarments() {
  const paths = Object.keys(imageModules)

  const garments = await Promise.all(
    paths.map(async (path) => {
      const filename = path.split('/').pop()
      const id       = filename.replace('.png', '')
      const image    = `/garments/${filename}`

      let meta
      try {
        meta = await analyzeGarment(image)
      } catch (err) {
        console.warn(`Could not analyze ${filename}:`, err.message)
        meta = fallbackMeta(id)
      }

      return { id, image, ...meta }
    })
  )

  return {
    all:   garments,
    upper: garments.filter(g => g.type === 'upper'),
    lower: garments.filter(g => g.type === 'lower'),
  }
}
