import { useEffect, useState } from 'react'
import type { AskResponse } from '@/lib/api'

export type Message = {
  id: number
  question: string
  response?: AskResponse
  error?: string
}

const MAX_SAVED = 50

function load(key: string): Message[] {
  try {
    const raw = localStorage.getItem(key)
    const parsed: Message[] = raw ? JSON.parse(raw) : []
    // A request that was in flight during a refresh will never finish.
    return parsed.map((m) =>
      m.response || m.error ? m : { ...m, error: 'This question was interrupted. Ask again.' },
    )
  } catch {
    return []
  }
}

export function usePersistedMessages(ownerId: string | undefined) {
  const key = ownerId ? `curated-ask-chat:${ownerId}` : null
  const [messages, setMessages] = useState<Message[]>(() => (key ? load(key) : []))

  // Reload if the signed-in account changes.
  useEffect(() => {
    setMessages(key ? load(key) : [])
  }, [key])

  useEffect(() => {
    if (!key) return
    try {
      localStorage.setItem(key, JSON.stringify(messages.slice(-MAX_SAVED)))
    } catch {
      /* storage full or blocked: the chat still works, it just won't persist */
    }
  }, [key, messages])

  return [messages, setMessages] as const
}
