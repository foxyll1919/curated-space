import { useNavigate, useParams } from 'react-router-dom'
import { ItemDetailDialog } from '@/components/ItemDetailDialog'

/**
 * `/item/:id` renders the same detail view as the grid dialog, so a screenshot
 * can be linked to directly and reloading it lands on the item rather than the
 * top of the library.
 */
export function ItemPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  return (
    <ItemDetailDialog
      id={id ?? null}
      onClose={() => {
        if (window.history.length > 1) navigate(-1)
        else navigate('/', { replace: true })
      }}
    />
  )
}