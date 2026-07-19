import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { useSendChatMessage } from '../../api/useChat';
import type { ChatMessage, ChatResponse } from '../../api/useChat';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';

// ---------------------------------------------------------------------------
// Agent config
// ---------------------------------------------------------------------------
const AGENTS = [
  { id: 'operations',  label: 'Operations' },
  { id: 'finance',     label: 'Finance' },
  { id: 'growth',      label: 'Growth' },
  { id: 'executive',   label: 'Executive' },
  { id: 'supplier',    label: 'Supplier' },
  { id: 'marketing',   label: 'Marketing' },
] as const;

type AgentId = typeof AGENTS[number]['id'];

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

// Each agent keeps its own history. Keyed by AgentId.
type AgentHistories = Partial<Record<AgentId, Message[]>>;

// ---------------------------------------------------------------------------
// Agent selector
// ---------------------------------------------------------------------------
function AgentSelector({
  active,
  onChange,
}: {
  active: AgentId;
  onChange: (id: AgentId) => void;
}) {
  return (
    <div className="flex gap-1 flex-wrap bg-parchment-dim rounded-ledger p-1">
      {AGENTS.map((agent) => (
        <button
          key={agent.id}
          onClick={() => onChange(agent.id)}
          className={`
            px-3 py-1.5 text-sm font-semibold rounded-[4px] transition-colors
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-gold
            ${active === agent.id
              ? 'bg-ink-navy text-parchment shadow-sm'
              : 'text-[#6B6455] hover:text-ink-navy hover:bg-white/60'
            }
          `}
        >
          {agent.label}
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Message components
// ---------------------------------------------------------------------------
function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[75%] bg-parchment-dim text-ink-navy text-sm font-body leading-relaxed px-4 py-3 rounded-ledger rounded-tr-sm">
        {content}
      </div>
    </div>
  );
}

function AssistantMessage({ content, agentLabel }: { content: string; agentLabel: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] font-body">
        {agentLabel}
      </span>
      <p className="text-sm font-body text-ink-navy leading-relaxed whitespace-pre-wrap">
        {content}
      </p>
    </div>
  );
}

function AssistantSkeleton({ agentLabel }: { agentLabel: string }) {
  return (
    <div className="flex flex-col gap-2 pt-1">
      <span className="text-[10px] font-semibold tracking-widest uppercase text-[#9AA0AE] font-body">
        {agentLabel}
      </span>
      <div className="flex flex-col gap-2">
        <Skeleton className="h-3.5 w-4/5" />
        <Skeleton className="h-3.5 w-3/5" />
        <Skeleton className="h-3.5 w-2/3" />
      </div>
    </div>
  );
}

function EmptyConversation({ agentLabel }: { agentLabel: string }) {
  return (
    <div className="flex-1 flex flex-col justify-center text-sm text-[#6B6455] font-body">
      <p className="font-semibold text-ink-navy mb-1">{agentLabel} agent</p>
      <p>Ask about anything in this agent's domain. Switch agents above to change context.</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Single-agent chat panel — memoised so switching agents unmounts/remounts
// ---------------------------------------------------------------------------
function AgentChatPanel({
  agentId,
  agentLabel,
  history,
  onHistoryChange,
}: {
  agentId: AgentId;
  agentLabel: string;
  history: Message[];
  onHistoryChange: (msgs: Message[]) => void;
}) {
  const [input, setInput] = useState('');
  const listRef = useRef<HTMLDivElement>(null);
  const sendMutation = useSendChatMessage(agentId);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [history, sendMutation.isPending]);

  function buildApiHistory(): ChatMessage[] {
    return history
      .slice(-20)
      .map((m) => ({ role: m.role, content: m.content }));
  }

  function handleSend() {
    const text = input.trim();
    if (!text || sendMutation.isPending) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text };
    const updated = [...history, userMsg];
    onHistoryChange(updated);
    setInput('');

    sendMutation.mutate(
      { message: text, history: buildApiHistory() },
      {
        onSuccess: (data: ChatResponse) => {
          const asst: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: data.reply,
          };
          onHistoryChange([...updated, asst]);
        },
        onError: () => {
          const errMsg: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: 'Sorry — something went wrong. Please try again.',
          };
          onHistoryChange([...updated, errMsg]);
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

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Message list */}
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto py-6 flex flex-col gap-6 pr-1"
      >
        {history.length === 0 && !sendMutation.isPending ? (
          <EmptyConversation agentLabel={agentLabel} />
        ) : (
          <>
            {history.map((msg) =>
              msg.role === 'user' ? (
                <UserBubble key={msg.id} content={msg.content} />
              ) : (
                <AssistantMessage key={msg.id} content={msg.content} agentLabel={agentLabel} />
              )
            )}
            {sendMutation.isPending && <AssistantSkeleton agentLabel={agentLabel} />}
          </>
        )}
      </div>

      {/* Input bar */}
      <div className="shrink-0 border-t border-parchment-dim pt-4 flex gap-3 items-end">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sendMutation.isPending}
          placeholder={`Ask ${agentLabel}… (Shift+Enter for newline)`}
          rows={1}
          className="
            flex-1 resize-none bg-white border border-parchment-dim rounded-ledger
            px-3.5 py-2.5 text-sm font-body text-ink-navy leading-relaxed
            outline-none transition-colors
            focus-visible:ring-2 focus-visible:ring-signal-gold
            disabled:opacity-50 max-h-[120px] overflow-y-auto
          "
        />
        <Button
          variant="primary"
          size="sm"
          disabled={sendMutation.isPending || !input.trim()}
          onClick={handleSend}
          className="shrink-0 self-end"
        >
          {sendMutation.isPending ? 'Sending…' : 'Send'}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export function OwnerChatPage() {
  const [activeAgent, setActiveAgent] = useState<AgentId>('operations');
  const [histories, setHistories] = useState<AgentHistories>({});

  function handleHistoryChange(agentId: AgentId, msgs: Message[]) {
    setHistories((prev) => ({ ...prev, [agentId]: msgs }));
  }

  const activeLabel = AGENTS.find((a) => a.id === activeAgent)?.label ?? activeAgent;

  return (
    <div className="flex flex-col h-full px-6 py-8 max-w-3xl mx-auto w-full">
      {/* Header */}
      <div className="shrink-0 mb-6">
        <h1 className="font-display font-semibold text-3xl text-ink-navy mb-4">
          Owner Chat
        </h1>
        <AgentSelector
          active={activeAgent}
          onChange={(id) => setActiveAgent(id)}
        />
      </div>

      {/* Chat panel — keyed so switching agents resets component state cleanly */}
      <AgentChatPanel
        key={activeAgent}
        agentId={activeAgent}
        agentLabel={activeLabel}
        history={histories[activeAgent] ?? []}
        onHistoryChange={(msgs) => handleHistoryChange(activeAgent, msgs)}
      />
    </div>
  );
}
