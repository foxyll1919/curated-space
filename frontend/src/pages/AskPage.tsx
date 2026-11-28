import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ArrowUpIcon,
  MessageSquarePlusIcon,
  SearchIcon,
  SquareIcon,
  Trash2Icon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { api } from '@/lib/api'
import type { StreamEvent } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { useConversations } from '@/hooks/useConversations'
import type { ChatMessage } from '@/hooks/useConversations'
import { cn } from 'cn'

const SUGGESTIONS = [
  'What design references have I saved?',
  'Show me screenshots related to dashboards',
  'Which screenshots mention authentication?',
]

// ---------------------------------------------------------------------------
// Lightweight inline markdown renderer
// ---------------------------------------------------------------------------

function MarkdownText({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g)
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**'))
          return (
            <strong key={i} className="font-semibold">
              {part.slice(2, -2)}
            </strong>
          )
        if (part.startsWith('*') && part.endsWith('*'))
          return (
            <em key={i} className="italic">
              {part.slice(1, -1)}
            </em>
          )
        if (part.startsWith('`') && part.endsWith('`'))
          return (
            <code key={i} className="rounded bg-muted px-1 py-0.5 text-[13px]">
              {part.slice(1, -1)}
            </code>
          )
        return <span key={i}>{part}</span>
      })}
    </span>
  )
}

function AnswerBlock({ text }: { text: string }) {
  const lines = text.split('\n')
  return (
    <div className="space-y-2 text-sm leading-7 text-foreground">
      {lines.map((line, i) => {
        const trimmed = line.trim()
        if (!trimmed) return <div key={i} className="h-2" />
        const bullet = trimmed.match(/^[-•*]\s+(.+)/)
        if (bullet) {
          return (
            <div key={i} className="flex gap-2 pl-2">
              <span className="mt-[11px] size-1 shrink-0 rounded-full bg-muted-foreground" />
              <MarkdownText text={bullet[1]!} />
            </div>
          )
        }
        const numbered = trimmed.match(/^(\d+)[.)]\s+(.+)/)
        if (numbered) {
          return (
            <div key={i} className="flex gap-2 pl-2">
              <span className="mt-0.5 shrink-0 text-xs font-medium text-muted-foreground">
                {numbered[1]}.
              </span>
              <MarkdownText text={numbered[2]!} />
            </div>
          )
        }
        return (
          <p key={i}>
            <MarkdownText text={trimmed} />
          </p>
        )
      })}
    </div>
  )
}

function StreamingCursor() {
  return <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-foreground" />
}

// ---------------------------------------------------------------------------
// Source card with image error fallback
// ---------------------------------------------------------------------------

function SourceCard({
  source,
}: {
  source: { id: string; title: string | null; description: string | null }
}) {
  const [imgError, setImgError] = useState(false)
  return (
    <a
      href={`/item/${source.id}`}
      className="block border border-border p-3 transition-colors hover:border-foreground"
    >
      <div className="mb-2 aspect-video overflow-hidden bg-muted">
        {imgError ? (
          <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
            No preview
          </div>
        ) : (
          <img
            src={api.imageUrl(source.id)}
            alt=""
            className="h-full w-full object-contain"
            loading="lazy"
            onError={() => setImgError(true)}
          />
        )}
      </div>
      <p className="line-clamp-2 text-sm text-foreground">
        {source.title || 'Untitled screenshot'}
      </p>
      {source.description ? (
        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{source.description}</p>
      ) : null}
    </a>
  )
}

// ---------------------------------------------------------------------------
// Message bubble
// ---------------------------------------------------------------------------

function MessageBubble({ message, isLatest }: { message: ChatMessage; isLatest: boolean }) {
  const answerText = message.streaming
    ? (message.streamedAnswer ?? '')
    : (message.response?.answer ?? '')
  const sources = message.response?.sources ?? []
  const toolTrace = message.response?.tool_trace ?? []
  const isInsufficient = message.response?.insufficient_evidence ?? false

  return (
    <article className="border-t border-border pt-5">
      <p className="mb-4 text-sm font-medium text-foreground">{message.question}</p>

      {/* Loading dots before first chunk arrives */}
      {message.streaming && !answerText && !message.error ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="flex gap-1">
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
          </span>
          Searching your library…
        </div>
      ) : null}

      {message.error ? (
        <Alert variant="destructive">
          <AlertTitle>Could not answer</AlertTitle>
          <AlertDescription>{message.error}</AlertDescription>
        </Alert>
      ) : null}

      {answerText ? (
        <div className="space-y-5">
          {toolTrace.length ? (
            <p className="text-xs text-muted-foreground">
              Tools used: {toolTrace.join(', ')}
            </p>
          ) : null}

          {isInsufficient && !message.streaming ? (
            <div className="rounded border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-xs text-amber-700 dark:text-amber-400">
              The answer may be incomplete — not enough matching screenshots were found.
            </div>
          ) : null}

          <div>
            <AnswerBlock text={answerText} />
            {message.streaming && isLatest ? <StreamingCursor /> : null}
          </div>

          {!message.streaming && sources.length ? (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Sources
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {sources.map((source) => (
                  <SourceCard key={source.id} source={source} />
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export function AskPage() {
  const { account } = useAuth()
  const {
    conversations,
    activeConversation,
    activeId,
    startNewConversation,
    selectConversation,
    deleteConversation,
    clearAllConversations,
    addMessage,
    updateMessage,
  } = useConversations(account?.id)

  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Refs for accumulating streamed text — avoids stale closures in the SSE
  // callback since React state updates are batched.
  const streamedTextRef = useRef('')
  const streamMetaRef = useRef({ convId: '', msgId: '', toolTrace: [] as string[] })

  const messages = activeConversation?.messages ?? []
  const messagesLen = messages.length
  const lastMessage = messages[messagesLen - 1] as ChatMessage | undefined
  const lastStreamedAnswer = lastMessage?.streamedAnswer

  // Auto-scroll when the message list grows or the latest streamed answer changes.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messagesLen, lastStreamedAnswer])

  const handleAbort = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])

  // Keep a stable ref to the current messages so the submit callback does not
  // need `messages` as a dependency (which changes on every render).
  const messagesRef = useRef(messages)
  useEffect(() => {
    messagesRef.current = messages
  })

  const submit = useCallback(() => {
    const trimmed = question.trim()
    if (!trimmed || busy) return

    setQuestion('')
    setBusy(true)
    streamedTextRef.current = ''

    // Build conversation history from prior completed messages.
    const currentMessages = messagesRef.current
    const history = currentMessages
      .filter((m) => m.response && !m.streaming)
      .slice(-6)
      .flatMap((m) => [
        { role: 'user' as const, content: m.question },
        ...(m.response ? [{ role: 'assistant' as const, content: m.response.answer }] : []),
      ])

    const { conversationId, messageId } = addMessage(trimmed)
    streamMetaRef.current = { convId: conversationId, msgId: messageId, toolTrace: [] }

    const controller = api.askStream(trimmed, history.slice(-12), (event: StreamEvent) => {
      const { convId, msgId } = streamMetaRef.current

      switch (event.type) {
        case 'tool_trace':
          streamMetaRef.current.toolTrace = event.tools
          break

        case 'answer_chunk':
          streamedTextRef.current += event.chunk
          updateMessage(convId, msgId, {
            streaming: true,
            streamedAnswer: streamedTextRef.current,
          })
          break

        case 'sources':
          updateMessage(convId, msgId, {
            streaming: false,
            streamedAnswer: undefined,
            response: {
              answer: streamedTextRef.current,
              sources: event.sources,
              insufficient_evidence: event.insufficient_evidence,
              tool_trace: streamMetaRef.current.toolTrace,
            },
          })
          break

        case 'error':
          updateMessage(convId, msgId, {
            streaming: false,
            streamedAnswer: undefined,
            error: event.message,
          })
          setBusy(false)
          break

        case 'done':
          setBusy(false)
          abortRef.current = null
          inputRef.current?.focus()
          break
      }
    })
    abortRef.current = controller

    controller.signal.addEventListener('abort', () => {
      const { convId, msgId } = streamMetaRef.current
      updateMessage(convId, msgId, {
        streaming: false,
        streamedAnswer: undefined,
        error: 'The request was cancelled.',
      })
      setBusy(false)
    })
  }, [question, busy, addMessage, updateMessage])

  return (
    <div className="flex min-h-[calc(100dvh-3.5rem)] w-full">
      {/* ---- Sidebar ---- */}
      <aside className="hidden w-56 shrink-0 border-r border-border lg:block">
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Conversations
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={startNewConversation}
              title="New conversation"
              aria-label="New conversation"
            >
              <MessageSquarePlusIcon className="size-3.5" />
            </Button>
          </div>

          <nav className="flex-1 overflow-y-auto">
            {conversations.length === 0 ? (
              <p className="p-3 text-xs text-muted-foreground">No conversations yet</p>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  className={cn(
                    'group flex w-full items-center gap-1.5 border-b border-border/50 px-3 py-2.5 text-left text-sm transition-colors',
                    conv.id === activeId
                      ? 'bg-muted/50 text-foreground'
                      : 'text-muted-foreground hover:bg-muted/30 hover:text-foreground',
                  )}
                >
                  <span className="flex-1 truncate">{conv.title}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteConversation(conv.id)
                    }}
                    className="hidden shrink-0 rounded p-0.5 text-muted-foreground hover:text-destructive group-hover:block"
                    title="Delete conversation"
                  >
                    <Trash2Icon className="size-3" />
                  </button>
                </button>
              ))
            )}
          </nav>

          {conversations.length > 0 ? (
            <div className="border-t border-border p-2">
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs text-muted-foreground"
                onClick={clearAllConversations}
              >
                Clear all
              </Button>
            </div>
          ) : null}
        </div>
      </aside>

      {/* ---- Main chat area ---- */}
      <div
        className="mx-auto flex flex-1 flex-col px-4 py-8 sm:px-6"
        style={{ maxWidth: '56rem' }}
      >
        <header className="mb-8 flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Your screenshot library</p>
            <h1 className="font-serif text-3xl italic text-balance text-foreground">Ask</h1>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden"
            onClick={startNewConversation}
          >
            <MessageSquarePlusIcon className="mr-1 size-3.5" />
            New
          </Button>
        </header>

        <div className="flex flex-1 flex-col gap-8">
          {messages.length === 0 ? (
            <div className="border-y border-border py-10">
              <SearchIcon className="mb-4 size-5 text-muted-foreground" />
              <p className="max-w-xl font-serif text-xl italic text-balance text-foreground">
                Ask about ideas, references and resources you have saved.
              </p>
              <p className="mt-2 max-w-xl text-sm text-pretty text-muted-foreground">
                Answers use your retrieved screenshots and include citations to the originals.
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      setQuestion(s)
                      inputRef.current?.focus()
                    }}
                    className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {messages.map((message, i) => (
            <MessageBubble
              key={message.id}
              message={message}
              isLatest={i === messages.length - 1}
            />
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* ---- Input ---- */}
        <form
          className="sticky bottom-0 flex items-end gap-2 border-t border-border bg-background py-4"
          onSubmit={(event) => {
            event.preventDefault()
            submit()
          }}
        >
          <div className="relative flex-1">
            <Textarea
              ref={inputRef}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask about your screenshots…"
              className="min-h-14 resize-none pr-20"
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  submit()
                }
              }}
            />
            <span className="pointer-events-none absolute bottom-2 right-3 text-[10px] text-muted-foreground/50">
              ↵ Send · ⇧↵ Newline
            </span>
          </div>
          {busy ? (
            <Button
              type="button"
              size="icon"
              variant="outline"
              onClick={handleAbort}
              aria-label="Stop"
              title="Stop generating"
            >
              <SquareIcon className="size-3.5" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              disabled={!question.trim()}
              aria-label="Ask"
              title="Send (Enter)"
            >
              <ArrowUpIcon />
            </Button>
          )}
        </form>
      </div>
    </div>
  )
}
