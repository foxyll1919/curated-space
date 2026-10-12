import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  CheckIcon,
  LoaderCircleIcon,
  PencilIcon,
  RefreshCwIcon,
  TrashIcon,
  TriangleAlertIcon,
  XIcon,
} from 'lucide-react'
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { StatusChip } from '@/components/StatusChip'
import { api, isApiError, labelEntries } from '@/lib/api'
import { formatDateTime } from '@/lib/dates'
import { itemFailureCopy } from '@/lib/failures'
import { useDeleteItem, useItem, usePatchItem, useReanalyze } from '@/hooks/useItems'

export function ItemDetailDialog({ id, onClose }: { id: string | null; onClose: () => void }) {
  return (
    <Dialog open={Boolean(id)} onOpenChange={(open: boolean) => !open && onClose()}>
      {id ? <ItemDetailBody id={id} onClose={onClose} /> : null}
    </Dialog>
  )
}

function ItemDetailBody({ id, onClose }: { id: string; onClose: () => void }) {
  const navigate = useNavigate()
  const { data: item, isPending, isError, error } = useItem(id)
  const patch = usePatchItem(id)
  const reanalyze = useReanalyze()
  const remove = useDeleteItem()

  const [editing, setEditing] = useState(false)
  const [draftTitle, setDraftTitle] = useState('')
  const [draftTags, setDraftTags] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)

  // Anything the backend owns cannot be corrected yet, so an open editor is
  // simply not shown while an item is in flight. Derived, so no effect is
  // needed to close it.
  const inFlight = item?.status === 'pending' || item?.status === 'processing'
  const isEditing = editing && !inFlight

  const startEditing = useCallback(() => {
    if (!item) return
    setDraftTitle(item.title ?? '')
    setDraftTags(item.tags.join(', '))
    setEditing(true)
  }, [item])

  const saveEdits = useCallback(() => {
    const title = draftTitle.trim()
    const tags = draftTags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)
      .slice(0, 8)

    if (!title) {
      toast.error('A screenshot needs a title.')
      return
    }
    patch.mutate(
      { title, tags },
      {
        onSuccess: () => {
          setEditing(false)
          toast.success('Saved.')
        },
        onError: (cause) => toast.error(cause.message),
      },
    )
  }, [draftTitle, draftTags, patch])

  if (isPending) {
    return (
      <DialogContent className="max-w-4xl rounded-none">
        <DialogHeader>
          <DialogTitle className="sr-only">Loading screenshot</DialogTitle>
          <DialogDescription className="sr-only">Fetching this screenshot.</DialogDescription>
        </DialogHeader>
        <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
          Loading
        </div>
      </DialogContent>
    )
  }

  if (isError || !item) {
    const notFound = isApiError(error) && error.isNotFound
    return (
      <DialogContent className="max-w-md rounded-none">
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">
            {notFound ? 'This screenshot is gone' : 'This screenshot could not be opened'}
          </DialogTitle>
          <DialogDescription>
            {notFound
              ? 'It was deleted, or it belongs to a different library.'
              : (error?.message ?? 'The server did not answer.')}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button onClick={onClose}>Back to the library</Button>
        </DialogFooter>
      </DialogContent>
    )
  }

  const labels = labelEntries(item)
  const failure = itemFailureCopy(item.error_code, item.status === 'deferred')
  const showRetry = item.status === 'failed' || item.status === 'deferred'

  return (
    <>
      <DialogContent className="max-h-[92dvh] overflow-y-auto rounded-none sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle className="font-serif text-xl leading-snug">
            {item.title ?? 'Untitled screenshot'}
          </DialogTitle>
<DialogDescription className="flex flex-col gap-0.5 font-mono text-xs">
            <span>Saved {formatDateTime(item.created_at)}</span>
            {item.analyzed_at ? <span>Analyzed {formatDateTime(item.analyzed_at)}</span> : null}
            {item.user_corrected ? <span>Corrected by you</span> : null}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-6 lg:flex-row">
<div className="flex min-w-0 flex-1 justify-center">
          <div className="flex w-fit items-start rounded-none border border-border bg-muted p-2">
            <img
              src={api.imageUrl(item.id)}
              alt={item.title ?? 'Saved screenshot'}
              className="max-h-[52dvh] w-auto max-w-full object-contain"
            />
          </div>
        </div>

        <div className="flex w-full shrink-0 flex-col gap-4 lg:w-72">
          <div className="flex flex-wrap items-center gap-2">
            <StatusChip status={item.status} />
            {labels.map(([name, value]) => (
              <span
                key={name}
                title={`${name}: ${value}`}
                className="rounded-none border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
              >
                {value}
              </span>
            ))}
          </div>

            {item.status === 'pending' || item.status === 'processing' ? (
              <div className="cs-shimmer h-24 rounded-none border border-border" role="status">
                <span className="sr-only">This screenshot is still being analyzed.</span>
              </div>
            ) : null}

            {showRetry ? (
              <Alert variant={item.status === 'failed' ? 'destructive' : 'default'}>
                {item.status === 'failed' ? <TriangleAlertIcon /> : <RefreshCwIcon />}
                <AlertTitle>{failure.headline}</AlertTitle>
                <AlertDescription className="flex flex-col items-start gap-3">
                  <span>{failure.detail}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={reanalyze.isPending}
                    onClick={() =>
                      reanalyze.mutate(item.id, {
                        onError: (cause) => toast.error(cause.message),
                      })
                    }
                  >
                    {reanalyze.isPending ? (
                      <LoaderCircleIcon data-icon="inline-start" className="animate-spin" />
                    ) : (
                      <RefreshCwIcon data-icon="inline-start" />
                    )}
                    Analyze now
                  </Button>
                </AlertDescription>
              </Alert>
            ) : null}

            <Separator decorative />

            {isEditing ? (
              <EditForm
                title={draftTitle}
                tags={draftTags}
                busy={patch.isPending}
                onTitle={setDraftTitle}
                onTags={setDraftTags}
                onSave={saveEdits}
                onCancel={() => setEditing(false)}
              />
            ) : (
              <div className="flex flex-col gap-4">
                <Field label="Title">
                  <p className="font-serif text-[17px] leading-snug">
                    {item.title ?? 'No title yet'}
                  </p>
                </Field>

                {item.description ? (
                  <Field label="Description">
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {item.description}
                    </p>
                  </Field>
                ) : null}

                <Field label="Tags">
                  {item.tags.length > 0 ? (
                    <ul className="flex flex-wrap gap-1.5">
                      {item.tags.map((tag) => (
                        <li
                          key={tag}
                          className="rounded-none border border-border px-1.5 py-0.5 text-xs text-muted-foreground"
                        >
                          {tag}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">No tags.</p>
                  )}
                </Field>
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="sm:justify-between">
          <Button
            variant="ghost"
            onClick={() => setConfirmOpen(true)}
            className="text-status-failed hover:text-status-failed"
          >
            <TrashIcon data-icon="inline-start" />
            Delete
          </Button>
          <div className="flex items-center gap-2">
            {!isEditing ? (
              <Button
                variant="outline"
                onClick={startEditing}
                disabled={inFlight}
                title={inFlight ? 'This screenshot is still being analyzed.' : undefined}
              >
                <PencilIcon data-icon="inline-start" />
                Edit title and tags
              </Button>
            ) : null}
            <Button variant="secondary" onClick={onClose}>
              Close
            </Button>
          </div>
        </DialogFooter>

        <p className="text-right font-mono text-[10px] text-muted-foreground/70">
          request {item.id}
        </p>
      </DialogContent>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent className="rounded-none">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-serif text-lg">
              Delete this screenshot permanently?
            </AlertDialogTitle>
            <AlertDialogDescription>
              The image and its description are removed from the library. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep it</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                remove.mutate(item.id, {
                  onSuccess: () => {
                    toast.success('Deleted.')
                    setConfirmOpen(false)
                    onClose()
                    navigate('/', { replace: true })
                  },
                  onError: (cause) => toast.error(cause.message),
                })
              }}
            >
              Delete permanently
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <Label className="font-mono text-[11px] tracking-wide text-muted-foreground uppercase">
        {label}
      </Label>
      {children}
    </div>
  )
}

function EditForm({
  title,
  tags,
  busy,
  onTitle,
  onTags,
  onSave,
  onCancel,
}: {
  title: string
  tags: string
  busy: boolean
  onTitle: (value: string) => void
  onTags: (value: string) => void
  onSave: () => void
  onCancel: () => void
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="edit-title">Title</Label>
        <Input
          id="edit-title"
          value={title}
          maxLength={80}
          onChange={(event) => onTitle(event.target.value)}
          disabled={busy}
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="edit-tags">Tags</Label>
        <Input
          id="edit-tags"
          value={tags}
          placeholder="Separate with commas, up to 8"
          onChange={(event) => onTags(event.target.value)}
          disabled={busy}
        />
        <p className="text-xs text-muted-foreground">
          {tags.split(',').filter((tag) => tag.trim()).length} of 8 used
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Button onClick={onSave} disabled={busy}>
          {busy ? (
            <LoaderCircleIcon data-icon="inline-start" className="animate-spin" />
          ) : (
            <CheckIcon data-icon="inline-start" />
          )}
          Save changes
        </Button>
        <Button variant="ghost" onClick={onCancel} disabled={busy}>
          <XIcon data-icon="inline-start" />
          Cancel
        </Button>
</div>
    </div>
  )
}

