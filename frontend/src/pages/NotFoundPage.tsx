import { Link } from 'react-router-dom'
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="mx-auto flex min-h-[60dvh] w-full max-w-2xl items-center px-4">
      <Empty className="w-full items-start">
        <EmptyHeader>
          <EmptyMedia variant="default" className="text-muted-foreground">
            404
          </EmptyMedia>
          <EmptyTitle className="font-serif text-2xl">That page is not in this library</EmptyTitle>
          <EmptyDescription>
            The link may be from an older version, or it may point at a screenshot that has been
            deleted.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button asChild>
            <Link to="/">Back to the library</Link>
          </Button>
        </EmptyContent>
      </Empty>
    </div>
  )
}