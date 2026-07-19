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

    // 2. Prepare payload
    const agentHistoryForApi: ChatMessage[] = currentMessages.map(m => ({
      role: m.role,
      content: m.content
    })).slice(-10);

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
    <div className="flex flex-col h-full bg-background relative">
      
      {/* Agent Selector */}
      <div className="px-6 py-4 bg-background border-b border-[#E8E3DA] z-10 sticky top-0 flex items-center justify-between">
        <div className="flex bg-surface-lighter border border-[#E8E3DA] rounded-md p-1 shadow-sm overflow-x-auto w-full sm:w-auto hide-scrollbar">
          {AGENTS.map((agent) => (
            <button
              key={agent.id}
              onClick={() => setActiveAgent(agent.id)}
              className={`px-3 py-1.5 text-xs font-semibold rounded whitespace-nowrap transition-colors duration-200 ${
                activeAgent === agent.id
                  ? 'bg-surface text-primary border border-[#E8E3DA] shadow-sm'
                  : 'text-text-muted hover:text-text-main hover:bg-[#E8E3DA]/30 border border-transparent'
              }`}
            >
              {agent.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col items-center">
        <div className="w-full max-w-3xl flex flex-col gap-6">
          
          {currentMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[40vh] text-center gap-4">
              <div className="w-12 h-12 rounded-full bg-surface-lighter border border-[#E8E3DA] flex items-center justify-center text-xl shadow-sm text-primary">
                ✦
              </div>
              <div>
                <h2 className="text-xl font-bold text-text-main mb-1">
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
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-surface border border-[#E8E3DA] flex items-center justify-center mr-3 shrink-0 text-xs font-bold text-primary">
                    AI
                  </div>
                )}
                <div className={`
                  max-w-[85%] sm:max-w-[75%] px-4 py-3 rounded-xl whitespace-pre-wrap leading-relaxed shadow-sm text-sm
                  ${msg.role === 'user' 
                    ? 'bg-primary text-white rounded-br-sm' 
                    : 'bg-surface border border-[#E8E3DA] text-text-main rounded-bl-sm'}
                `}>
                  {msg.content}
                </div>
              </div>
            ))
          )}

          {isPending && (
            <div className="flex w-full justify-start">
              <div className="w-8 h-8 rounded-full bg-surface border border-[#E8E3DA] flex items-center justify-center mr-3 shrink-0 text-xs font-bold text-primary">
                AI
              </div>
              <div className="max-w-[75%] px-5 py-4 rounded-xl bg-surface border border-[#E8E3DA] rounded-bl-sm flex flex-col gap-2.5 min-w-[200px] shadow-sm">
                <Skeleton className="h-3 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
                <Skeleton className="h-3 w-5/6" />
              </div>
            </div>
          )}
          <div ref={bottomRef} className="h-4" />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 bg-background border-t border-[#E8E3DA] shrink-0">
        <div className="max-w-3xl mx-auto relative flex items-end gap-3">
          <textarea
            className="w-full bg-surface border border-[#E8E3DA] rounded-xl px-4 py-3 pr-14 text-sm text-text-main placeholder-text-muted resize-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors min-h-[50px] max-h-[150px] overflow-y-auto shadow-sm"
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
            className="absolute right-2 bottom-1.5 rounded-lg p-2 h-auto w-auto"
            aria-label="Send"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </Button>
        </div>
      </div>
      
    </div>
  );
}
