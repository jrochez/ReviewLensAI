'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { AuthGuard } from '@/components/layout/AuthGuard'
import { TopNav } from '@/components/layout/TopNav'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { datasetsApi, chatApi } from '@/lib/api'
import { ChatMessage, Dataset } from '@/types'
import { Send, ArrowLeft } from 'lucide-react'

const SUGGESTIONS = [
  'What are the most common complaints?',
  'What do reviewers say about quality?',
  'What features do customers love most?',
]

function ChatBubble({ msg }: { msg: ChatMessage }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[75%] bg-accent text-white rounded-xl rounded-tr-sm px-4 py-3 text-sm">
          {msg.content}
        </div>
      </div>
    )
  }

  if (msg.scope_refused) {
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-[75%] bg-scope-guard-bg border border-dashed border-scope-guard-border rounded-xl px-4 py-3 text-sm text-text-secondary italic">
          {msg.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[75%] bg-surface border border-border rounded-xl rounded-tl-sm px-4 py-3 text-sm shadow-sm">
        <div className="text-xs text-text-secondary mb-1">ReviewLens AI</div>
        <div className="whitespace-pre-wrap">{msg.content}</div>
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { id } = useParams<{ id: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { data: ds, isError: dsError } = useQuery({
    queryKey: ['dataset', id],
    queryFn: () => datasetsApi.get(id),
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const sendMessage = async (text: string) => {
    if (!text.trim() || sending) return
    setError('')
    const userMsg: ChatMessage = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setSending(true)

    try {
      const history = messages.slice(-10)
      const res = await chatApi.send(id, text, history)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.reply,
        scope_refused: res.scope_refused,
      }])
    } catch (err: any) {
      setError(err?.data?.message || 'Something went wrong. Please try again.')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
        scope_refused: false,
      }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <AuthGuard>
      <div className="flex flex-col h-screen">
        <TopNav />
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <aside className="w-56 border-r border-border bg-surface flex flex-col shrink-0">
            <div className="flex-1 overflow-y-auto py-3">
              {ds && (
                <Link href={`/datasets/${id}`} className="flex items-center gap-2 px-4 py-2.5 text-sm bg-accent-subtle border-l-[3px] border-accent text-accent font-medium hover:bg-accent/10 transition-colors">
                  <span className="w-1.5 h-1.5 rounded-full shrink-0 bg-accent" />
                  <span className="truncate">{ds.product_name || ds.asin}</span>
                </Link>
              )}
            </div>
            <div className="p-4 border-t border-border">
              <Link href="/datasets" className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary">
                <ArrowLeft size={14} /> All Datasets
              </Link>
            </div>
          </aside>

          {/* Chat panel */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Context header */}
            {dsError ? (
              <div className="px-6 py-3 border-b border-border bg-white">
                <p className="text-error text-sm">Failed to load dataset info.</p>
              </div>
            ) : ds && (
              <div className="px-6 py-3 border-b border-border bg-white">
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-text-primary">{ds.product_name || ds.asin}</span>
                  <StatusBadge status={ds.status} />
                  {ds.review_count && <span className="text-xs text-text-secondary">{ds.review_count.toLocaleString()} reviews</span>}
                </div>
              </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4" aria-live="polite">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full gap-4">
                  <p className="text-text-secondary text-sm">Ask a question about these reviews</p>
                  <div className="flex flex-wrap gap-2 justify-center max-w-md">
                    {SUGGESTIONS.map(s => (
                      <button
                        key={s}
                        onClick={() => sendMessage(s)}
                        className="px-3 py-2 text-xs border border-border rounded-full hover:bg-raised text-text-secondary hover:text-text-primary transition-colors"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((msg, i) => <ChatBubble key={i} msg={msg} />)}
              {sending && (
                <div className="flex justify-start mb-4">
                  <div className="bg-surface border border-border rounded-xl rounded-tl-sm px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce [animation-delay:0ms]" />
                      <div className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce [animation-delay:150ms]" />
                      <div className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce [animation-delay:300ms]" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="px-6 py-4 border-t border-border bg-white">
              <div className="flex items-end gap-3 border border-border rounded-xl overflow-hidden bg-white focus-within:ring-2 focus-within:ring-accent">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question about these reviews…"
                  rows={1}
                  className="flex-1 px-4 py-3 text-sm resize-none focus:outline-none bg-transparent"
                  style={{ maxHeight: '112px', overflowY: 'auto' }}
                  disabled={sending || ds?.status !== 'ready'}
                />
                <button
                  onClick={() => sendMessage(input)}
                  disabled={!input.trim() || sending || ds?.status !== 'ready'}
                  className="mr-3 mb-3 w-8 h-8 bg-accent text-white rounded-lg flex items-center justify-center hover:bg-accent-hover disabled:opacity-40 transition-colors"
                  aria-label="Send"
                >
                  <Send size={14} />
                </button>
              </div>
              <p className="text-xs text-text-disabled mt-1">Enter to send · Shift+Enter for newline</p>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
