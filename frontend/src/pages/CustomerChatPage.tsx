import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { useSendChatMessage } from '../api/useChat';
import type { ChatMessage, ChatResponse } from '../api/useChat';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';

// ---------------------------------------------------------------------------
// Shared Types & Hooks (same logic)
// ---------------------------------------------------------------------------
export function CustomerChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  
  const bottomRef = useRef<HTMLDivElement>(null);
  
  const { mutate: sendMessage, isPending } = useSendChatMessage();

  // Scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isPending]);

  const handleSend = () => {
    const text = inputValue.trim();
    if (!text) return;

    // 1. Append user message
    const newMsg: ChatMessage = { role: 'user', content: text };
    const updatedHistory = [...messages, newMsg];
    setMessages(updatedHistory);
    setInputValue('');

    // 2. Call API, sending up to last 10 messages for context
    const historyForApi = updatedHistory.slice(-10);
    
    sendMessage(
      { agent_name: 'customer-ai', message: text, history: historyForApi },
      {
        onSuccess: (data: ChatResponse) => {
          setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
        },
        onError: () => {
          setMessages((prev) => [
            ...prev, 
            { role: 'assistant', content: 'An error occurred. Please try again later.' }
          ]);
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
    <div className="min-h-screen bg-background text-text-main flex flex-col font-sans relative overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-secondary/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="px-6 py-4 border-b border-white/10 bg-surface/50 backdrop-blur-md sticky top-0 z-10 flex items-center justify-between">
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
          Brisq Support
        </h1>
        <span className="text-xs font-medium px-3 py-1 bg-white/5 rounded-full text-text-muted border border-white/10">
          Powered by AI
        </span>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col items-center z-10">
        <div className="w-full max-w-2xl flex flex-col gap-6">
          
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[40vh] text-center gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-primary to-secondary p-0.5 shadow-glow">
                <div className="w-full h-full bg-surface rounded-full flex items-center justify-center text-2xl">
                  ✨
                </div>
              </div>
              <div>
                <h2 className="text-2xl font-bold mb-2">How can we help?</h2>
                <div className="text-text-muted flex flex-col gap-2">
                  <p>— Track order status and estimated delivery</p>
                  <p>— Check refund eligibility and request status</p>
                  <p>— Inquire about product stock and availability</p>
                  <p>— Review return, shipping, and cancellation policies</p>
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div 
                key={i} 
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
      </main>

      {/* Input Area */}
      <footer className="p-4 bg-surface/50 backdrop-blur-md border-t border-white/10 z-10">
        <div className="max-w-2xl mx-auto relative flex items-end gap-3">
          <textarea
            className="w-full bg-surface/80 border border-white/10 rounded-2xl px-5 py-4 pr-16 text-sm text-text-main placeholder-text-muted resize-none focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all min-h-[60px] max-h-[200px] overflow-y-auto shadow-glass"
            placeholder="Ask about your order, a refund, or store policy..."
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
      </footer>
    </div>
  );
}
