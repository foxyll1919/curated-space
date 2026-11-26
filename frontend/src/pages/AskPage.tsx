import { useState, useRef, useEffect } from 'react'
import {
  ArrowUpIcon,
  SearchIcon,
  PlusIcon,
  Trash2Icon,
  MessageSquareIcon,
  PanelLeftCloseIcon,
  PanelLeftIcon,
  SparklesIcon,
  ClockIcon,
  XIcon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ScrollArea } from '@/components/ui/scroll-area'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { useConversations } from '@/hooks/useConversations'
import { cn } from 'cn'

const STARTER_SUGGESTIONS = [
  'Find design inspiration for mobile app navigation',
  'What color palette ideas did I save in my library?',
  'Show me saved references with charts or dashboard layouts',
  'Summarize key typography and card patterns in screenshots',
]

function formatRelativeTime(timestamp: number): string {
  const diffSec = Math.floor((Date.now() - timestamp) / 1000)
  if (diffSec < 60) return 'Just now'
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHours = Math.floor(diffMin / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays}d ago`
  return new Date(timestamp).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })
}

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
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [confirmClear, setConfirmClear] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const currentMessages = activeConversation?.messages ?? []

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentMessages.length, busy])

  async function handleSend(textToSend?: string) {
    const raw = textToSend ?? question
    const trimmed = raw.trim()
    if (!trimmed || busy) return

    // Prepare multi-turn history from current conversation
    const history = currentMessages
      .slice(-6)
      .flatMap((msg) => [
        { role: 'user' as const, content: msg.question },
        ...(msg.response
          ? [{ role: 'assistant' as const, content: msg.response.answer }]
          : []),
      ])

    const { conversationId, messageId } = addMessage(trimmed)
    setQuestion('')
    setBusy(true)

    try {
      const response = await api.ask(trimmed, history)
      updateMessage(conversationId, messageId, { response })
    } catch (error) {
      updateMessage(conversationId, messageId, {
        error: error instanceof Error ? error.message : 'The request failed.',
      })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex h-[calc(100dvh-3.5rem)] w-full overflow-hidden bg-background">
      {/* Mobile sidebar overlay backdrop */}
      {sidebarOpen ? (
        <div
          className="fixed inset-0 z-30 bg-background/80 backdrop-blur-xs md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      {/* Conversation History Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-14 left-0 z-40 flex w-72 flex-col border-r border-border bg-background transition-all duration-200 md:static md:z-auto',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:hidden',
        )}
      >
        {/* Sidebar Header */}
        <div className="flex h-14 items-center justify-between border-b border-border px-4">
          <div className="flex items-center gap-2">
            <MessageSquareIcon className="size-4 text-muted-foreground" />
            <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              History
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="xs"
              onClick={() => {
                startNewConversation()
                if (window.innerWidth < 768) setSidebarOpen(false)
              }}
              className="gap-1 text-xs"
            >
              <PlusIcon className="size-3.5" />
              New Chat
            </Button>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => setSidebarOpen(false)}
              className="md:hidden"
              aria-label="Close history"
            >
              <XIcon className="size-4" />
            </Button>
          </div>
        </div>

        {/* Conversations List */}
        <ScrollArea className="flex-1">
          <div className="flex flex-col gap-1 p-2">
            {conversations.length === 0 ? (
              <div className="px-3 py-8 text-center">
                <ClockIcon className="mx-auto mb-2 size-4 text-muted-foreground" />
                <p className="text-xs text-muted-foreground">No saved conversations yet.</p>
                <p className="mt-1 text-[11px] text-muted-foreground/80">
                  Ask a question to start one.
                </p>
              </div>
            ) : (
              conversations.map((conv) => {
                const isActive = conv.id === activeId
                const messageCount = conv.messages.length

                return (
                  <div
                    key={conv.id}
                    onClick={() => {
                      selectConversation(conv.id)
                      if (window.innerWidth < 768) setSidebarOpen(false)
                    }}
                    className={cn(
                      'group relative flex cursor-pointer flex-col rounded-none border border-transparent p-2.5 text-left transition-colors',
                      isActive
                        ? 'border-border bg-muted text-foreground'
                        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground',
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="line-clamp-1 text-xs font-medium text-foreground">
                        {conv.title || 'Untitled conversation'}
                      </p>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteConversation(conv.id)
                        }}
                        className="opacity-0 transition-opacity group-hover:opacity-100 hover:text-destructive focus:opacity-100"
                        title="Delete conversation"
                        aria-label={`Delete ${conv.title}`}
                      >
                        <Trash2Icon className="size-3.5 text-muted-foreground hover:text-destructive" />
                      </button>
                    </div>

                    <div className="mt-1.5 flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>{formatRelativeTime(conv.updatedAt)}</span>
                      <span>
                        {messageCount} {messageCount === 1 ? 'msg' : 'msgs'}
                      </span>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </ScrollArea>

        {/* Sidebar Footer */}
        {conversations.length > 0 ? (
          <div className="border-t border-border p-2">
            {confirmClear ? (
              <div className="flex items-center justify-between gap-2 px-2 py-1">
                <span className="text-xs text-destructive">Clear all?</span>
                <div className="flex items-center gap-1">
                  <Button
                    variant="destructive"
                    size="xs"
                    onClick={() => {
                      clearAllConversations()
                      setConfirmClear(false)
                    }}
                  >
                    Yes, clear
                  </Button>
                  <Button
                    variant="ghost"
                    size="xs"
                    onClick={() => setConfirmClear(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirmClear(true)}
                className="w-full justify-start gap-2 text-xs text-muted-foreground hover:text-destructive"
              >
                <Trash2Icon className="size-3.5" />
                Clear conversation history
              </Button>
            )}
          </div>
        ) : null}
      </aside>

      {/* Main Chat Workspace */}
      <div className="flex flex-1 flex-col min-w-0 h-full overflow-hidden">
        {/* Workspace Sub-header */}
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4 sm:px-6">
          <div className="flex items-center gap-3 min-w-0">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setSidebarOpen((prev) => !prev)}
              aria-label={sidebarOpen ? 'Collapse history' : 'Open history'}
              title={sidebarOpen ? 'Collapse history' : 'Open history'}
            >
              {sidebarOpen ? (
                <PanelLeftCloseIcon className="size-4" />
              ) : (
                <PanelLeftIcon className="size-4" />
              )}
            </Button>
            <div className="min-w-0">
              <h1 className="truncate font-serif text-base text-foreground sm:text-lg">
                {activeConversation?.title || 'Ask'}
              </h1>
              <p className="hidden text-[11px] text-muted-foreground sm:block">
                Screenshot library reasoning and visual search
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {activeConversation ? (
              <Button
                variant="outline"
                size="xs"
                onClick={startNewConversation}
                className="gap-1 text-xs"
              >
                <PlusIcon className="size-3.5" />
                New Chat
              </Button>
            ) : null}
          </div>
        </div>

        {/* Message Stream */}
        <ScrollArea className="flex-1 px-4 py-6 sm:px-8">
          <div className="mx-auto flex max-w-3xl flex-col gap-8">
            {currentMessages.length === 0 ? (
              <div className="py-8">
                <div className="border-y border-border py-8">
                  <SearchIcon className="mb-4 size-5 text-muted-foreground" />
                  <h2 className="max-w-xl font-serif text-2xl text-foreground">
                    Ask about ideas, references and resources you have saved.
                  </h2>
                  <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                    Answers use your retrieved screenshots and include citations to the originals.
                  </p>
                </div>

                <div className="mt-8">
                  <p className="mb-3 flex items-center gap-1.5 font-mono text-xs uppercase tracking-wider text-muted-foreground">
                    <SparklesIcon className="size-3.5" />
                    Suggested queries
                  </p>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {STARTER_SUGGESTIONS.map((suggestion) => (
                      <button
                        key={suggestion}
                        type="button"
                        onClick={() => void handleSend(suggestion)}
                        className="rounded-none border border-border p-3 text-left text-xs text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {currentMessages.map((message) => (
              <article key={message.id} className="border-t border-border pt-6 first:border-t-0 first:pt-0">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                    You
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {formatRelativeTime(message.createdAt)}
                  </span>
                </div>
                <p className="mb-5 text-sm font-medium text-foreground">{message.question}</p>

                {busy && !message.response && !message.error ? (
                  <div className="flex items-center gap-2 py-3 text-sm text-muted-foreground">
                    <span className="size-2 animate-pulse rounded-full bg-foreground" />
                    Searching screenshots and reasoning…
                  </div>
                ) : null}

                {message.error ? (
                  <Alert variant="destructive">
                    <AlertTitle>Could not answer</AlertTitle>
                    <AlertDescription>{message.error}</AlertDescription>
                  </Alert>
                ) : null}

                {message.response ? (
                  <div className="space-y-5">
                    {message.response.tool_trace?.length ? (
                      <p className="text-xs text-muted-foreground">
                        Tools used: {message.response.tool_trace.join(', ')}
                      </p>
                    ) : null}
                    <p className="whitespace-pre-wrap text-sm leading-7 text-foreground">
                      {message.response.answer}
                    </p>
                    {message.response.sources.length ? (
                      <div className="border-t border-border/60 pt-4">
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                          Sources
                        </p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {message.response.sources.map((source) => (
                            <a
                              key={source.id}
                              href={`/item/${source.id}`}
                              className="block border border-border p-3 transition-colors hover:border-foreground"
                            >
                              <div className="mb-2 aspect-video overflow-hidden bg-muted">
                                <img
                                  src={api.imageUrl(source.id)}
                                  alt=""
                                  className="h-full w-full object-contain"
                                />
                              </div>
                              <p className="line-clamp-2 text-sm text-foreground">
                                {source.title || 'Untitled screenshot'}
                              </p>
                              {source.description ? (
                                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                                  {source.description}
                                </p>
                              ) : null}
                            </a>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </article>
            ))}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Question Prompt Input */}
        <div className="border-t border-border bg-background p-4 sm:px-8">
          <form
            className="mx-auto flex max-w-3xl items-end gap-2"
            onSubmit={(event) => {
              event.preventDefault()
              void handleSend()
            }}
          >
            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask about your screenshots… (Enter to send, Shift+Enter for new line)"
              className="min-h-12 max-h-36 resize-none rounded-none text-sm"
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  void handleSend()
                }
              }}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!question.trim() || busy}
              aria-label="Ask"
              className="rounded-none shrink-0"
            >
              <ArrowUpIcon className="size-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
