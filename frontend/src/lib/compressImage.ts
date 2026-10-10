export const MAX_EDGE_PX = 1280
export const JPEG_QUALITY = 0.8

/** Scale so the long edge is at most maxEdge. Never upscales. */
export function fitWithin(width: number, height: number, maxEdge = MAX_EDGE_PX): { width: number; height: number } {
  const longEdge = Math.max(width, height)
  if (longEdge <= maxEdge) return { width, height }
  const scale = maxEdge / longEdge
  return { width: Math.round(width * scale), height: Math.round(height * scale) }
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error("We couldn't open that photo. Try a JPEG or PNG."))
    }
    img.src = url
  })
}

/** Compress a photo client-side to JPEG (max 1280 px long edge, quality 0.8). */
export async function compressImage(file: File): Promise<Blob> {
  const img = await loadImage(file)
  const { width, height } = fitWithin(img.naturalWidth, img.naturalHeight)
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Your browser could not process the photo.')
  ctx.drawImage(img, 0, 0, width, height)
  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('Could not compress the photo.'))), 'image/jpeg', JPEG_QUALITY),
  )
}
