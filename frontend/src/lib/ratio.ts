import type { Item } from '@/lib/api'

/**
 * The ratio a card should render at, derived from the dimensions the backend
 * already reports for the sanitized image.
 *
 * Clamped at both ends so a banner or a very long capture cannot dominate a
 * whole column. The card letterboxes the image inside this box, so a
 * screenshot is never cropped to fit and never stretched out of shape.
 */
export function itemRatio(item: Pick<Item, 'image'>): number | null {
  const { width, height } = item.image
  // A placeholder for a just-accepted upload has no dimensions yet.
  if (!width || !height) return null
  return Math.min(Math.max(height / width, 0.45), 2.6)
}