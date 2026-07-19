import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent, FormEvent } from 'react';
import { useSendChatMessage } from '../api/useChat';
import type { ChatMessage, ChatResponse } from '../api/useChat';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------
function EmptyState() {
  return (
    <div className="flex-1 flex flex-col items-start justify-center px-6 pb-6">
      <p className="text-sm font-semibold text-ink-navy mb-2 tracking-wide uppercase font-body">
        What this can help with
      </p>
      <ul className="text-[#6B6455] text-sm font-body leading-relaxed space-y-1.5 list-none">
        <li>— Order status and estimated delivery</li>
        <li>— Refund eligibility and request status</li>
        <li>— Product stock and availability</li>
        <li>— Return, shipping, and cancellation policies</li>
      </ul>
      <p className="mt-6 text-xs text-[#9AA0AE]">
        For issues with your account or payment, contact support directly.
      </p>
    </div>
  );
}

function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[75%] bg-parchment-dim text-ink-navy text-sm font-body leading-relaxed px-4 py-3 rounded-ledger rounded-tr-sm">
        {content}
      </div>
    </div>
  );
}

function AssistantMessage({ content }: { content: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] font-body">
        Brisq
      </span>
      <p className="text-sm font-body text-ink-navy leading-relaxed">
        {content}
      </p>
    </div>
  );
}

function AssistantSkeleton() {
  return (
    <div className="flex flex-col gap-2 pt-1">
      <span className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] font-body">
        Brisq
      </span>
      <div className="flex flex-col gap-2">
        <Skeleton className="h-3.5 w-4/5" />
        <Skeleton className="h-3.5 w-3/5" />
        <Skeleton className="h-3.5 w-2/3" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
const MAX_HISTORY_TURNS = 10; // last N user+assistant pairs

export function CustomerChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const listRef = useRef<HTMLDivElement>(null);

  const sendMutation = useSendChatMessage('customer');

  // Scroll to bottom whenever messages change or while loading
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, sendMutation.isPending]);

  function buildHistory(): ChatMessage[] {
    // Take the last MAX_HISTORY_TURNS messages as alternating user/assistant pairs
    return messages
      .slice(-MAX_HISTORY_TURNS * 2)
      .map((m) => ({ role: m.role, content: m.content }));
  }

  function handleSend() {
    const text = input.trim();
    if (!text || sendMutation.isPending) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    sendMutation.mutate(
      { message: text, history: buildHistory() },
      {
        onSuccess: (data: ChatResponse) => {
          const assistantMsg: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: data.reply,
          };
          setMessages((prev) => [...prev, assistantMsg]);
        },
        onError: () => {
          // useToast is already called inside useSendChatMessage onError
          // Optionally also append an inline error message
          const errMsg: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: 'Sorry — something went wrong. Please try again.',
          };
          setMessages((prev) => [...prev, errMsg]);
        },
      }
    );
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    handleSend();
  }

  const isEmpty = messages.length === 0 && !sendMutation.isPending;

  return (
    <div className="min-h-screen bg-parchment flex flex-col items-center">
      {/* Container */}
      <div className="w-full max-w-[720px] flex flex-col h-screen">

        {/* Header */}
        <header className="shrink-0 border-b border-parchment-dim px-6 py-5">
          <span className="font-display font-semibold text-xl text-ink-navy">
            Brisq
          </span>
          <p className="text-xs text-[#9AA0AE] mt-0.5 font-body">
            Store assistant
          </p>
        </header>

        {/* Message list */}
        <div
          ref={listRef}
          className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-6"
        >
          {isEmpty ? (
            <EmptyState />
          ) : (
            <>
              {messages.map((msg) =>
                msg.role === 'user' ? (
                  <UserBubble key={msg.id} content={msg.content} />
                ) : (
                  <AssistantMessage key={msg.id} content={msg.content} />
                )
              )}
              {sendMutation.isPending && <AssistantSkeleton />}
            </>
          )}
        </div>

        {/* Divider */}
        <div className="shrink-0 border-t border-parchment-dim" />

        {/* Input bar */}
        <form
          onSubmit={handleSubmit}
          className="shrink-0 px-6 py-4 flex gap-3 items-end"
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={sendMutation.isPending}
            placeholder="Ask about your order, a refund, or store policy…"
            rows={1}
            className="
              flex-1 resize-none bg-white border border-parchment-dim rounded-ledger
              px-3.5 py-2.5 text-sm font-body text-ink-navy leading-relaxed
              outline-none transition-colors
              focus-visible:ring-2 focus-visible:ring-signal-gold
              disabled:opacity-50
              max-h-[120px] overflow-y-auto
            "
            style={{ fieldSizing: 'content' } as React.CSSProperties}
          />
          <Button
            type="submit"
            variant="primary"
            size="sm"
            disabled={sendMutation.isPending || !input.trim()}
            className="shrink-0 self-end"
          >
            {sendMutation.isPending ? 'Sending…' : 'Send'}
          </Button>
        </form>

      </div>
    </div>
  );
}
