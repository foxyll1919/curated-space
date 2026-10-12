import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type Item, type ItemStatus } from '@/lib/api'
import { ApiError } from '@/lib/errors'

/** The backend's own upload limit is 10 per 60s. */
const MAX_BYTES = 8 * 1024 * 1024
const ACCEPTED_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/bmp'])

/**
 * Two at a time. The server limit is 10 per minute, so a burst of twenty
 * screenshots becomes ten orderly requests rather than twenty rejections.
 */
const CONCURRENCY = 2

const MAX_ATTEMPTS = 4
const RATE_LIMIT_PAUSE_MS = 15_000

export type UploadJobState = 'queued' | 'uploading' | 'waiting' | 'accepted' | 'failed'

export type UploadJob = {
  localId: string
  name: string
  byteSize: number
  state: UploadJobState
  attempts: number
  /** Set once the backend has accepted the file and given us an item id. */
  itemId?: string
  itemStatus?: ItemStatus
  error?: string
  rateLimited?: boolean
}

type QueuedJob = { localId: string; file: File; skipAnalysis: boolean }

function validate(file: File): string | null {
  if (!ACCEPTED_TYPES.has(file.type)) {
    return `${file.name} is not an image the backend accepts. Use a PNG, JPEG, WebP, GIF or BMP.`
  }
  if (file.size > MAX_BYTES) {
    const mib = (file.size / 1024 / 1024).toFixed(1)
    return `${file.name} is ${mib} MB. The limit is 8 MB.`
  }
  if (file.size === 0) {
    return `${file.name} is empty.`
  }
  return null
}

let localIdCounter = 0

/**
 * A client-side upload queue.
 *
 * Files are validated before anything is sent, then uploaded two at a time. A
 * 429 does not fail the upload: the file waits out the server's fixed window
 * and tries again, and the caller learns about it through `rateLimited` so it
 * can say so.
 */
export function useUploadQueue(handlers?: { onAccepted?: (job: UploadJob) => void }) {
  const [jobs, setJobs] = useState<UploadJob[]>([])
  const [rateLimitNote, setRateLimitNote] = useState<string | null>(null)

  const queueRef = useRef<QueuedJob[]>([])
  const activeRef = useRef(0)
  const mountedRef = useRef(true)
  const handlersRef = useRef(handlers)

  useEffect(() => {
    handlersRef.current = handlers
  }, [handlers])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      queueRef.current = []
    }
  }, [])

  const patchJob = useCallback((localId: string, patch: Partial<UploadJob>) => {
    setJobs((current) =>
      current.map((job) => (job.localId === localId ? { ...job, ...patch } : job)),
    )
  }, [])

  const send = useCallback(
    async (entry: QueuedJob) => {
      let attempts = 0
      for (;;) {
        attempts += 1
        if (!mountedRef.current) return
        patchJob(entry.localId, { state: 'uploading', attempts, rateLimited: false })
        try {
          const accepted = await api.upload(entry.file, entry.skipAnalysis)
          if (!mountedRef.current) return
          setRateLimitNote(null)
          const job: UploadJob = {
            localId: entry.localId,
            name: entry.file.name,
            byteSize: entry.file.size,
            state: 'accepted',
            attempts,
            itemId: accepted.id,
            itemStatus: (accepted.status as ItemStatus) ?? 'pending',
          }
          patchJob(entry.localId, job)
          handlersRef.current?.onAccepted?.(job)
          return
        } catch (cause) {
          if (!mountedRef.current) return
          if (cause instanceof ApiError && cause.isRateLimited && attempts < MAX_ATTEMPTS) {
            setRateLimitNote(
              'You are uploading faster than the limit allows. The rest of this batch is waiting.',
            )
            patchJob(entry.localId, {
              state: 'waiting',
              attempts,
              rateLimited: true,
              error: 'Waiting for the upload limit to reset.',
            })
            await new Promise((resolve) => window.setTimeout(resolve, RATE_LIMIT_PAUSE_MS))
            continue
          }
          const message =
            cause instanceof ApiError
              ? cause.message
              : 'That file could not be uploaded.'
          patchJob(entry.localId, { state: 'failed', attempts, error: message })
          return
        }
      }
    },
    [patchJob],
  )

  /**
   * Starts as many queued uploads as the concurrency budget allows. Declared as
   * a function declaration so the recursive call below is not a reference to a
   * binding that is still being initialised.
   */
  function pump() {
    while (activeRef.current < CONCURRENCY && queueRef.current.length > 0) {
      const entry = queueRef.current.shift()
      if (!entry) return
      activeRef.current += 1
      void send(entry).finally(() => {
        activeRef.current -= 1
        pump()
      })
    }
  }

  const enqueue = useCallback(
    (files: File[], skipAnalysis: boolean) => {
      const accepted: UploadJob[] = []
      const next: QueuedJob[] = []

      for (const file of files) {
        const localId = `local-${(localIdCounter += 1)}`
        const problem = validate(file)
        const job: UploadJob = {
          localId,
          name: file.name,
          byteSize: file.size,
          state: problem ? 'failed' : 'queued',
          attempts: 0,
          error: problem ?? undefined,
        }
        accepted.push(job)
        if (!problem) next.push({ localId, file, skipAnalysis })
      }

      setJobs((current) => [...current, ...accepted])
      queueRef.current = [...queueRef.current, ...next]
      pump()
      return accepted
    },
    // `pump` reads refs only and is re-created every render, so the callback
    // does not need it as a dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  )

  const dismiss = useCallback((localId: string) => {
    setJobs((current) => current.filter((job) => job.localId !== localId))
  }, [])

  const clearSettled = useCallback(() => {
    setJobs((current) =>
      current.filter(
        (job) => job.state === 'queued' || job.state === 'uploading' || job.state === 'waiting',
      ),
    )
  }, [])

  const isBusy = jobs.some(
    (job) => job.state === 'queued' || job.state === 'uploading' || job.state === 'waiting',
  )

  return { jobs, enqueue, dismiss, clearSettled, isBusy, rateLimitNote }
}

/**
 * Builds a placeholder item so a freshly accepted upload can appear in the
 * grid immediately, before the first poll resolves it. The image dimensions
 * are unknown until the item is fetched, so the card reserves a default ratio
 * and the real one replaces it on the first poll.
 */
export function placeholderItem(job: UploadJob): Item | null {
  if (!job.itemId) return null
  const now = new Date().toISOString()
  return {
    id: job.itemId,
    status: job.itemStatus ?? 'pending',
    image: { mime: 'image/png', width: 0, height: 0, byte_size: job.byteSize },
    title: null,
    description: null,
    tags: [],
    labels: {},
    abstained: false,
    classifier_score: null,
    taxonomy_version: null,
    classifier_version: null,
    extractor_model: null,
    prompt_version: null,
    error_code: null,
    user_corrected: false,
    created_at: now,
    updated_at: now,
    analyzed_at: null,
  }
}

export const UPLOAD_MAX_BYTES = MAX_BYTES