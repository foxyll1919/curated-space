/**
 * Item-level `error_code` values the pipeline can store. The set is defined by
 * the backend, not by this client; unknown codes fall back to a generic line
 * rather than leaking a raw identifier into the interface as an explanation.
 */
const FAILURE_COPY: Record<string, { headline: string; detail: string; retryable: boolean }> = {
  analysis_failed: {
    headline: 'Analysis did not finish',
    detail: 'The image was saved. The metadata step did not complete.',
    retryable: true,
  },
  extraction_failed: {
    headline: 'Analysis did not finish',
    detail: 'The image was saved, but the description step did not complete.',
    retryable: true,
  },
  extraction_provider_error: {
    headline: 'The analysis service did not respond',
    detail: 'The image was saved. The model could not be reached, so nothing was described.',
    retryable: true,
  },
  extraction_invalid: {
    headline: 'The description came back unreadable',
    detail: 'The image was saved, but the response did not match the expected shape.',
    retryable: true,
  },
  extraction_blocked: {
    headline: 'The analysis service declined',
    detail: 'The image was saved. The provider rejected the request.',
    retryable: true,
  },
  extraction_empty: {
    headline: 'Nothing was found in this screenshot',
    detail: 'The image was saved, but the description came back empty.',
    retryable: true,
  },
  extraction_truncated: {
    headline: 'The description was cut short',
    detail: 'The image was saved, but the response ended before it was complete.',
    retryable: true,
  },
  analysis_disabled: {
    headline: 'Analysis is turned off',
    detail: 'The image was saved. Analysis is disabled for this server.',
    retryable: true,
  },
  analysis_skipped: {
    headline: 'Saved without analysis',
    detail: 'The image was saved and nothing was sent for analysis.',
    retryable: true,
  },
  budget_exceeded: {
    headline: 'Waiting on the analysis budget',
    detail: 'The image was saved. Analysis resumes once the budget allows it.',
    retryable: true,
  },
  rate_limited: {
    headline: 'The analysis service is busy',
    detail: 'The image was saved. Too many analyses ran at once.',
    retryable: true,
  },
}

const UNKNOWN_FAILURE = {
  headline: 'Analysis did not finish',
  detail: 'The image was saved. The backend reported a problem it could not explain.',
  retryable: true,
}

const UNKNOWN_DEFERRAL = {
  headline: 'Saved, not analyzed',
  detail: 'The image was saved. Analysis was deferred for a reason the backend did not name.',
  retryable: true,
}

export type ItemFailureCopy = (typeof FAILURE_COPY)[string]

export function itemFailureCopy(
  errorCode: string | null | undefined,
  deferred: boolean,
): ItemFailureCopy {
  if (errorCode) {
    const known = FAILURE_COPY[errorCode]
    if (known) return known
  }
  return deferred ? UNKNOWN_DEFERRAL : UNKNOWN_FAILURE
}