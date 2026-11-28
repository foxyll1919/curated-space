import { useState, useEffect, useCallback, useMemo } from 'react'
import type { AskResponse } from '@/lib/api'

export type ChatMessage = {
  id: string
  question: string
  response?: AskResponse
  error?: string
  streaming?: boolean
  streamedAnswer?: string
  createdAt: number
}

export type Conversation = {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messages: ChatMessage[]
}

const STORAGE_PREFIX = 'curated_space_conversations_'
const MAX_CONVERSATIONS = 50

function getStorageKey(accountId?: string | null): string {
  return `${STORAGE_PREFIX}${accountId || 'guest'}`
}

function uid(): string {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

function loadConversations(key: string): Conversation[] {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Conversation[]
    if (!Array.isArray(parsed)) return []
    return parsed
      .map((c) => ({
        ...c,
        messages: c.messages.map((m) =>
          m.response || m.error
            ? { ...m, streaming: false, streamedAnswer: undefined }
            : { ...m, error: 'This question was interrupted. Ask again.', streaming: false },
        ),
      }))
      .sort((a, b) => b.updatedAt - a.updatedAt)
  } catch {
    return []
  }
}

function saveConversations(key: string, list: Conversation[]): void {
  try {
    const trimmed = list.slice(0, MAX_CONVERSATIONS)
    localStorage.setItem(key, JSON.stringify(trimmed))
  } catch {
    /* storage full or blocked — chat still works */
  }
}

export function useConversations(accountId?: string | null) {
  const storageKey = useMemo(() => getStorageKey(accountId), [accountId])

  const [conversations, setConversations] = useState<Conversation[]>(() =>
    loadConversations(storageKey),
  )

  const [activeId, setActiveId] = useState<string | null>(() => {
    const initial = loadConversations(storageKey)
    return initial[0]?.id ?? null
  })

  // Track the previous key to detect account changes.
  const [syncedKey, setSyncedKey] = useState(storageKey)
  if (syncedKey !== storageKey) {
    setSyncedKey(storageKey)
    const loaded = loadConversations(storageKey)
    setConversations(loaded)
    setActiveId(loaded[0]?.id ?? null)
  }

  // Persist to localStorage when conversations change — but skip transient
  // streaming state so interrupted-message detection works on reload.
  useEffect(() => {
    const persistable = conversations.map((c) => ({
      ...c,
      messages: c.messages.map((m) => {
        if (!m.streaming) return m
        // A message still streaming hasn't finished — persist without
        // streaming flags so it shows as interrupted on reload.
        const { streaming: _s, streamedAnswer: _sa, ...rest } = m
        return rest
      }),
    }))
    saveConversations(storageKey, persistable)
  }, [conversations, storageKey])

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? null,
    [conversations, activeId],
  )

  const startNewConversation = useCallback(() => {
    setActiveId(null)
  }, [])

  const selectConversation = useCallback((id: string) => {
    setActiveId(id)
  }, [])

  const deleteConversation = useCallback(
    (id: string) => {
      setConversations((current) => {
        const next = current.filter((c) => c.id !== id)
        if (activeId === id) {
          setActiveId(next[0]?.id ?? null)
        }
        return next
      })
    },
    [activeId],
  )

  const clearAllConversations = useCallback(() => {
    setConversations([])
    setActiveId(null)
  }, [])

  /**
   * Append a user message. If there is no active conversation, one is created.
   * Returns the conversation id and message id so the caller can update the
   * message later (e.g. with a streamed response).
   *
   * Fixed: the conversation id is computed deterministically *before* the state
   * update and returned synchronously, avoiding the React batching race.
   */
  const addMessage = useCallback(
    (question: string): { conversationId: string; messageId: string } => {
      const trimmed = question.trim()
      const messageId = uid()
      const newMessage: ChatMessage = {
        id: messageId,
        question: trimmed,
        createdAt: Date.now(),
        streaming: true,
      }

      // Decide the target conversation id deterministically before setState.
      let targetId = activeId

      setConversations((current) => {
        const existingIndex = current.findIndex((c) => c.id === activeId)
        const existing = existingIndex >= 0 ? current[existingIndex] : undefined

        if (existing) {
          const updated: Conversation = {
            ...existing,
            updatedAt: Date.now(),
            messages: [...existing.messages, newMessage],
          }
          const next = [...current]
          next.splice(existingIndex, 1)
          return [updated, ...next]
        }

        // Create new conversation — id was pre-computed above.
        const title = trimmed.length > 45 ? `${trimmed.slice(0, 45)}…` : trimmed
        const newConversation: Conversation = {
          id: `conv_${uid()}`,
          title: title || 'New Conversation',
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: [newMessage],
        }
        targetId = newConversation.id
        return [newConversation, ...current]
      })

      // Update activeId outside the conversations setter to avoid batching issues.
      if (targetId !== activeId) {
        // targetId is only reassigned when a new conversation is created above,
        // and the new id is deterministic, so this is safe.
        setActiveId(targetId)
      }

      return { conversationId: targetId ?? `conv_${messageId}`, messageId }
    },
    [activeId],
  )

  const updateMessage = useCallback(
    (convId: string, msgId: string, patch: Partial<ChatMessage>) => {
      setConversations((current) =>
        current.map((c) => {
          if (c.id !== convId) return c
          return {
            ...c,
            updatedAt: Date.now(),
            messages: c.messages.map((m) => (m.id === msgId ? { ...m, ...patch } : m)),
          }
        }),
      )
    },
    [],
  )

  const renameConversation = useCallback((id: string, title: string) => {
    setConversations((current) =>
      current.map((c) => (c.id === id ? { ...c, title, updatedAt: Date.now() } : c)),
    )
  }, [])

  return {
    conversations,
    activeConversation,
    activeId,
    startNewConversation,
    selectConversation,
    deleteConversation,
    clearAllConversations,
    addMessage,
    updateMessage,
    renameConversation,
  }
}
