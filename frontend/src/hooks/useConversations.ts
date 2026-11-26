import { useState, useEffect, useCallback, useMemo } from 'react'
import type { AskResponse } from '@/lib/api'

export type ChatMessage = {
  id: number
  question: string
  response?: AskResponse
  error?: string
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

function getStorageKey(accountId?: string | null): string {
  return `${STORAGE_PREFIX}${accountId || 'guest'}`
}

function loadConversations(key: string): Conversation[] {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Conversation[]
    if (!Array.isArray(parsed)) return []
    return parsed.sort((a, b) => b.updatedAt - a.updatedAt)
  } catch {
    return []
  }
}

function saveConversations(key: string, list: Conversation[]): void {
  try {
    localStorage.setItem(key, JSON.stringify(list))
  } catch (err) {
    console.error('Failed to save conversations to localStorage', err)
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

  // Synchronize when storageKey changes (e.g. account switch) during render pattern
  const [syncedKey, setSyncedKey] = useState(storageKey)
  if (syncedKey !== storageKey) {
    setSyncedKey(storageKey)
    const loaded = loadConversations(storageKey)
    setConversations(loaded)
    setActiveId(loaded[0]?.id ?? null)
  }

  // Sync state changes to localStorage
  useEffect(() => {
    saveConversations(storageKey, conversations)
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

  const addMessage = useCallback(
    (question: string) => {
      const trimmed = question.trim()
      const messageId = Date.now()
      const newMessage: ChatMessage = {
        id: messageId,
        question: trimmed,
        createdAt: Date.now(),
      }

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

        // Create new conversation
        const title = trimmed.length > 45 ? `${trimmed.slice(0, 45)}…` : trimmed
        const newConversation: Conversation = {
          id: `conv_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
          title: title || 'New Conversation',
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: [newMessage],
        }
        targetId = newConversation.id
        return [newConversation, ...current]
      })

      if (targetId && targetId !== activeId) {
        setActiveId(targetId)
      }

      return { conversationId: targetId ?? `conv_${messageId}`, messageId }
    },
    [activeId],
  )

  const updateMessage = useCallback(
    (convId: string, msgId: number, patch: Partial<ChatMessage>) => {
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
  }
}
