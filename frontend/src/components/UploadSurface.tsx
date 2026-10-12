import { useCallback, useEffect, useRef, useState } from 'react'
import { ImagePlusIcon, ShieldIcon, XIcon } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { useUploadQueue, type UploadJob } from '@/hooks/useUpload'
import { cn } from 'cn'

export type UploadSurfaceProps = {
  onAccepted: (job: UploadJob) => void
}

/** Rows shown before the batch is collapsed behind a "Show all" control. */
const VISIBLE_JOBS = 4

function readFiles(list: FileList | null): File[] {
  return list ? Array.from(list) : []
}

/** Only screenshots are accepted, so files from a paste or a drop are typed first. */
function looksLikeImage(file: File): boolean {
  return file.type.startsWith('image/')
}

/**
 * The three ways a screenshot arrives: dropped, picked, or pasted. All three
 * funnel into the same validation and the same upload queue.
 *
 * This is deliberately one short band rather than a panel. The library is the
 * point, so the way in stays a single strip above it.
 */
export function UploadSurface({ onAccepted }: UploadSurfaceProps) {
  const [skipAnalysis, setSkipAnalysis] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [showAllJobs, setShowAllJobs] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)
  const dragDepth = useRef(0)

  const { jobs, enqueue, dismiss, clearSettled, isBusy, rateLimitNote } = useUploadQueue({
    onAccepted,
  })

  const submit = useCallback(
    (files: File[]) => {
      const images = files.filter(looksLikeImage)
      const rejected = files.length - images.length
      if (rejected > 0) {
        toast.error(
          `${rejected} ${rejected === 1 ? 'file was' : 'files were'} skipped. Only images can be saved.`,
        )
      }
      if (images.length === 0) return

      const added = enqueue(images, skipAnalysis)
      const refused = added.filter((job) => job.state === 'failed')
      if (refused.length > 0) {
        toast.error(refused[0]?.error ?? 'That file could not be saved.')
      }
      const queued = added.length - refused.length
      if (queued > 0) {
        toast(
          `${queued} ${queued === 1 ? 'screenshot is' : 'screenshots are'} saving.`,
        )
      }
    },
    [enqueue, skipAnalysis],
  )

  // Paste is the path most people take with a screenshot, so it is bound
  // globally rather than only while the band has focus.
  useEffect(() => {
    function onPaste(event: ClipboardEvent) {
      const files = readFiles(event.clipboardData?.files ?? null)
      if (files.length === 0) return
      event.preventDefault()
      submit(files)
    }
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  }, [submit])

  function onDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault()
    dragDepth.current = 0
    setDragging(false)
    submit(readFiles(event.dataTransfer.files))
  }

  const settledJobs = jobs.filter((job) => job.state === 'accepted' || job.state === 'failed')
  /*
    A long batch would otherwise push the library itself off the screen, so the
    list is capped. Anything unfinished is always inside the first rows, because
    accepted and failed entries are appended in the order they finish.
  */
  const inFlightJobs = jobs.filter((job) => job.state !== 'accepted' && job.state !== 'failed')
  const settledTail = jobs.filter((job) => job.state === 'accepted' || job.state === 'failed')
  const visibleJobs = showAllJobs
    ? jobs
    : [...inFlightJobs, ...settledTail].slice(0, VISIBLE_JOBS)

  return (
    <section aria-label="Save screenshots" className="flex flex-col gap-3">
      <div
        onDragEnter={(event) => {
          event.preventDefault()
          dragDepth.current += 1
          setDragging(true)
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          event.preventDefault()
          dragDepth.current -= 1
          if (dragDepth.current <= 0) setDragging(false)
        }}
        onDrop={onDrop}
        className={cn(
          'flex flex-col gap-3 rounded-none border border-dashed px-4 py-3',
          'transition-colors duration-150 sm:flex-row sm:items-center sm:justify-between',
          dragging ? 'border-ring bg-ring/6' : 'border-border bg-card/40',
        )}
      >
        <div className="flex flex-col gap-0.5">
          <p className="text-sm font-medium text-foreground">
            {dragging ? 'Drop to save' : 'Drop screenshots here, or paste from the clipboard'}
          </p>
          <p className="text-xs text-muted-foreground">
            PNG, JPEG, WebP, GIF or BMP, up to 8 MB each.
          </p>
        </div>

        <Button onClick={() => inputRef.current?.click()} className="shrink-0 self-start sm:self-auto">
          <ImagePlusIcon data-icon="inline-start" />
          Choose files
        </Button>

        {/*
          The privacy toggle is given its own labelled block and a sentence of
          explanation, because turning it on changes who can see the image.
        */}
        <div className="flex shrink-0 items-start gap-2.5 border-t border-border pt-3 sm:border-t-0 sm:pt-0">
          <Switch
            id="skip-analysis"
            checked={skipAnalysis}
            onCheckedChange={setSkipAnalysis}
            className="mt-0.5"
            aria-describedby="skip-analysis-description"
          />
          <div className="flex flex-col gap-0.5">
            <Label htmlFor="skip-analysis" className="text-sm font-medium">
              Don&apos;t analyze
            </Label>
            <p id="skip-analysis-description" className="max-w-[26ch] text-xs text-muted-foreground">
              Keeps it on your machine, sent to no AI provider.
            </p>
          </div>
          <ShieldIcon aria-hidden="true" className="mt-0.5 hidden size-4 text-muted-foreground sm:block" />
        </div>

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          className="sr-only"
          aria-label="Choose screenshot files"
          onChange={(event) => {
            submit(readFiles(event.target.files))
            event.target.value = ''
          }}
        />
      </div>

      {rateLimitNote ? (
        <p role="status" className="text-sm text-status-deferred">
          {rateLimitNote}
        </p>
      ) : null}

      {jobs.length > 0 ? (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <p className="font-mono text-[11px] tracking-wide text-muted-foreground uppercase">
              This batch
            </p>
            <div className="flex items-center gap-1">
              {jobs.length > VISIBLE_JOBS ? (
                <Button variant="ghost" size="xs" onClick={() => setShowAllJobs((open) => !open)}>
                  {showAllJobs ? 'Show less' : `Show all ${jobs.length}`}
                </Button>
              ) : null}
              {settledJobs.length > 0 ? (
                <Button variant="ghost" size="xs" onClick={clearSettled}>
                  Clear finished
                </Button>
              ) : null}
            </div>
          </div>
          <ul className="flex flex-col">
            {visibleJobs.map((job) => (
              <li
                key={job.localId}
                className="flex items-center gap-3 border-b border-border py-1.5 text-sm last:border-b-0"
              >
                <span className="min-w-0 flex-1 truncate text-foreground">{job.name}</span>
                <span
                  className={cn(
                    'shrink-0 font-mono text-[11px]',
                    job.state === 'failed' ? 'text-status-failed' : 'text-muted-foreground',
                  )}
                >
                  {JOB_TEXT[job.state]}
                </span>
                {job.state === 'failed' || job.state === 'accepted' ? (
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    onClick={() => dismiss(job.localId)}
                    aria-label={`Dismiss ${job.name}`}
                  >
                    <XIcon />
                  </Button>
                ) : null}
              </li>
            ))}
          </ul>
          {isBusy ? (
            <p aria-live="polite" className="sr-only">
              Uploading. {jobs.length - settledJobs.length} still to go.
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}

const JOB_TEXT: Record<UploadJob['state'], string> = {
  queued: 'Waiting',
  uploading: 'Saving',
  waiting: 'Rate limited',
  accepted: 'Saved',
  failed: 'Failed',
}