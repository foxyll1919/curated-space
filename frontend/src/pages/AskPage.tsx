import { useState } from 'react'
import { ArrowUpIcon, SearchIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { api, type AskResponse } from '@/lib/api'

type Message = {
  id: number
  question: string
  response?: AskResponse
  error?: string
}

export function AskPage() {
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])

  async function submit() {
    const trimmed = question.trim()
    if (!trimmed || busy) return
    const id = Date.now()
    setMessages((current) => [...current, { id, question: trimmed }])
    setQuestion('')
    setBusy(true)
    try {
      const history = messages
        .slice(-6)
        .flatMap((message) => [
          { role: 'user' as const, content: message.question },
          ...(message.response
            ? [{ role: 'assistant' as const, content: message.response.answer }]
            : []),
        ])
      const response = await api.ask(trimmed, history)
      setMessages((current) =>
        current.map((message) => (message.id === id ? { ...message, response } : message)),
      )
    } catch (error) {
      setMessages((current) =>
        current.map((message) =>
          message.id === id
            ? { ...message, error: error instanceof Error ? error.message : 'The request failed.' }
            : message,
        ),
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-3.5rem)] w-full max-w-4xl flex-col px-4 py-8 sm:px-6">
      <header className="mb-8">
        <p className="text-sm text-muted-foreground">Your screenshot library</p>
        <h1 className="font-serif text-3xl text-foreground">Ask</h1>
      </header>

      <div className="flex flex-1 flex-col gap-8">
        {messages.length === 0 ? (
          <div className="border-y border-border py-10">
            <SearchIcon className="mb-4 size-5 text-muted-foreground" />
            <p className="max-w-xl font-serif text-xl text-foreground">
              Ask about ideas, references and resources you have saved.
            </p>
            <p className="mt-2 max-w-xl text-sm text-muted-foreground">
              Answers use your retrieved screenshots and include citations to the originals.
            </p>
          </div>
        ) : null}

        {messages.map((message) => (
          <article key={message.id} className="border-t border-border pt-5">
            <p className="mb-4 text-sm font-medium text-foreground">{message.question}</p>
            {busy && !message.response && !message.error ? (
              <p className="text-sm text-muted-foreground">Searching and reasoning…</p>
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
                  <div>
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
      </div>

      <form
        className="sticky bottom-0 flex items-end gap-2 border-t border-border bg-background py-4"
        onSubmit={(event) => {
          event.preventDefault()
          void submit()
        }}
      >
        <Textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about your screenshots…"
          className="min-h-14 resize-none"
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void submit()
            }
          }}
        />
        <Button type="submit" size="icon" disabled={!question.trim() || busy} aria-label="Ask">
          <ArrowUpIcon />
        </Button>
      </form>
    </div>
  )
}
