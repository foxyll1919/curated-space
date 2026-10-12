import { useEffect, useRef, useState } from 'react'
import { cn } from 'cn'

/** The grid's row track. Cards span a whole number of these. */
const ROW_PX = 8
/** Vertical breathing room, applied inside the card rather than by row-gap. */
const CARD_GAP_PX = 16
/** Fixed caption band, so the height maths below is exact. */
const CAPTION_PX = 76

type MasonryItemProps = {
  /** width / height from the API. A freshly accepted upload has neither. */
  ratio: number | null
  children: React.ReactNode
  className?: string
}

/**
 * One cell of the masonry grid.
 *
 * CSS grid with a fixed row track does not know how tall a screenshot should
 * be, so each cell measures its own column width and converts that into a row
 * span. The card then fills exactly that span and the image is letterboxed
 * inside it, which means a screenshot is never cropped to fit and never
 * stretched out of shape.
 */
export function MasonryItem({ ratio, children, className }: MasonryItemProps) {
  const ref = useRef<HTMLLIElement | null>(null)
  const [span, setSpan] = useState<number | undefined>(undefined)

  useEffect(() => {
    const node = ref.current
    if (!node) return

    function measure(width: number) {
      // An unknown aspect ratio falls back to a plain 3:4 until the first poll
      // brings the real dimensions.
      const aspect = ratio && Number.isFinite(ratio) ? ratio : 0.75
      const needed = width * aspect + CAPTION_PX + CARD_GAP_PX
      setSpan(Math.ceil(needed / ROW_PX))
    }

    measure(node.getBoundingClientRect().width)
    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width
      if (width) measure(width)
    })
    observer.observe(node)
    return () => observer.disconnect()
  }, [ratio])

  return (
    <li
      ref={ref}
      style={span ? { gridRowEnd: `span ${span}` } : undefined}
      className={cn('min-h-0', className)}
    >
      {children}
    </li>
  )
}

export const MASONRY_CAPTION_PX = CAPTION_PX