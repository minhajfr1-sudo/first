const BASE_URL = import.meta.env.VITE_MODAL_API_URL || 'http://localhost:8000'

/**
 * Process the user's photo once on upload.
 * Modal extracts pose + body segmentation and returns a session token.
 */
export async function processPhoto(photoFile) {
  const form = new FormData()
  form.append('person_image', photoFile)

  const res = await fetch(`${BASE_URL}/process-photo`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || 'Failed to process photo')
  }

  return res.json() // { session_id: string }
}

/**
 * Run virtual try-on for a single garment.
 * Returns a base64-encoded result image.
 */
export async function runTryOn(sessionId, garmentUrl, garmentType) {
  const res = await fetch(`${BASE_URL}/tryon`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      garment_url: garmentUrl,   // full public Netlify URL to the garment PNG
      garment_type: garmentType, // "upper" | "lower"
    }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || 'Try-on failed')
  }

  const data = await res.json() // { result_image: "base64..." }
  return `data:image/png;base64,${data.result_image}`
}

/**
 * Warm up the Modal container so the first real request is fast.
 * Call this as soon as the user's photo is processed.
 */
export async function warmUp() {
  try {
    await fetch(`${BASE_URL}/ping`, { method: 'GET' })
  } catch {
    // silence — warm-up is best-effort
  }
}
