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
type SessionHistory = Record<AgentId, Message[]>;

function generateId() {
  return Math.random().toString(36).substring(2, 9);
}

export function OwnerChatPage() {
  const [activeAgent, setActiveAgent] = useState<AgentId>('operations');
  const [historyMap, setHistoryMap] = useState<SessionHistory>({
    operations: [], finance: [], growth: [],
    executive: [], supplier: [], marketing: []
  });
  const [inputValue, setInputValue] = useState('');
  
  const bottomRef = useRef<HTMLDivElement>(null);
  const { mutate: sendMessage, isPending } = useSendChatMessage();

  const currentMessages = historyMap[activeAgent];

  // Scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages, isPending]);

  const handleSend = () => {
    const text = inputValue.trim();
    if (!text) return;

    // 1. Optimistic user message
    const userMsg: Message = { id: generateId(), role: 'user', content: text };
    
    setHistoryMap(prev => ({
      ...prev,
      [activeAgent]: [...prev[activeAgent], userMsg]
    }));
    setInputValue('');

    // 2. Prepare payload (convert to what the API expects)
    const agentHistoryForApi: ChatMessage[] = currentMessages.map(m => ({
      role: m.role,
      content: m.content
    })).slice(-10); // keep last 10 for context

    // 3. Fire mutation
    sendMessage(
      { 
        agent_name: activeAgent, 
        message: text,
        history: agentHistoryForApi
      },
      {
        onSuccess: (data: ChatResponse) => {
          const aiMsg: Message = { id: generateId(), role: 'assistant', content: data.reply };
          setHistoryMap(prev => ({
            ...prev,
            [activeAgent]: [...prev[activeAgent], aiMsg]
          }));
        },
        onError: () => {
          const errMsg: Message = { id: generateId(), role: 'assistant', content: 'Agent failed to respond.' };
          setHistoryMap(prev => ({
            ...prev,
            [activeAgent]: [...prev[activeAgent], errMsg]
          }));
        }
      }
    );
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full relative">
      
      {/* Agent Selector (Glass Header) */}
      <div className="px-6 py-4 bg-surface/50 backdrop-blur-md border-b border-white/10 z-10 sticky top-0 flex items-center justify-between">
        <div className="flex bg-background border border-white/10 rounded-xl overflow-hidden shadow-glass p-1">
          {AGENTS.map((agent) => (
            <button
              key={agent.id}
              onClick={() => setActiveAgent(agent.id)}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                activeAgent === agent.id
                  ? 'bg-primary/20 text-primary shadow-[0_0_10px_rgba(139,92,246,0.2)]'
                  : 'text-text-muted hover:text-text-main hover:bg-white/5'
              }`}
            >
              {agent.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center">
        <div className="w-full max-w-3xl flex flex-col gap-6">
          
          {currentMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[40vh] text-center gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-primary to-secondary p-0.5 shadow-glow">
                <div className="w-full h-full bg-surface rounded-full flex items-center justify-center text-2xl">
                  🤖
                </div>
              </div>
              <div>
                <h2 className="text-xl font-bold mb-1">
                  {AGENTS.find(a => a.id === activeAgent)?.label} Agent
                </h2>
                <p className="text-text-muted text-sm">Send a message to begin the session.</p>
              </div>
            </div>
          ) : (
            currentMessages.map((msg) => (
              <div 
                key={msg.id} 
                className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`
                  max-w-[85%] sm:max-w-[75%] px-5 py-3.5 rounded-2xl whitespace-pre-wrap leading-relaxed shadow-glass
                  ${msg.role === 'user' 
                    ? 'bg-primary-gradient text-white rounded-br-sm' 
                    : 'bg-surface border border-white/10 text-text-main rounded-bl-sm'}
                `}>
                  {msg.content}
                </div>
              </div>
            ))
          )}

          {isPending && (
            <div className="flex w-full justify-start">
              <div className="max-w-[75%] px-5 py-4 rounded-2xl bg-surface border border-white/10 rounded-bl-sm flex flex-col gap-3 min-w-[200px]">
                <Skeleton className="h-4 w-3/4 bg-white/5" />
                <Skeleton className="h-4 w-1/2 bg-white/5" />
                <Skeleton className="h-4 w-5/6 bg-white/5" />
              </div>
            </div>
          )}
          <div ref={bottomRef} className="h-4" />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-6 bg-surface/50 backdrop-blur-md border-t border-white/10 z-10 shrink-0">
        <div className="max-w-3xl mx-auto relative flex items-end gap-3">
          <textarea
            className="w-full bg-surface/80 border border-white/10 rounded-2xl px-5 py-4 pr-16 text-sm text-text-main placeholder-text-muted resize-none focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all min-h-[60px] max-h-[200px] overflow-y-auto shadow-glass"
            placeholder={`Message ${AGENTS.find(a => a.id === activeAgent)?.label} agent...`}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isPending}
            rows={1}
          />
          <Button 
            onClick={handleSend} 
            disabled={isPending || !inputValue.trim()}
            variant="primary"
            className="absolute right-2 bottom-2 rounded-xl p-2.5 h-auto w-auto"
            aria-label="Send"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </Button>
        </div>
      </div>
      
    </div>
  );
}
