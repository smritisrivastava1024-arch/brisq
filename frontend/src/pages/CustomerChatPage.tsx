import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { useSendChatMessage } from '../api/useChat';
import type { ChatMessage, ChatResponse } from '../api/useChat';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';

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
    <div className="min-h-screen bg-background text-text-main flex flex-col font-sans">
      {/* Header */}
      <header className="px-6 py-4 border-b border-[#E8E3DA] bg-background sticky top-0 z-10 flex items-center justify-between">
        <h1 className="text-xl font-bold text-primary tracking-tight">
          Brisq Support
        </h1>
        <span className="text-xs font-medium px-2.5 py-1 bg-surface-lighter rounded-md text-text-muted border border-[#E8E3DA]">
          Powered by AI
        </span>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col items-center">
        <div className="w-full max-w-2xl flex flex-col gap-6">
          
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[40vh] text-center gap-4">
              <div className="w-12 h-12 rounded-full bg-surface-lighter border border-[#E8E3DA] flex items-center justify-center text-xl shadow-sm text-primary">
                ✦
              </div>
              <div>
                <h2 className="text-xl font-bold text-text-main mb-2">How can we help?</h2>
                <div className="text-text-muted flex flex-col gap-2 text-sm">
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
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-surface border border-[#E8E3DA] flex items-center justify-center mr-3 shrink-0 text-xs font-bold text-primary">
                    B
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
                B
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
      </main>

      {/* Input Area */}
      <footer className="p-4 bg-background border-t border-[#E8E3DA] z-10">
        <div className="max-w-2xl mx-auto relative flex items-end gap-3">
          <textarea
            className="w-full bg-surface border border-[#E8E3DA] rounded-xl px-4 py-3 pr-14 text-sm text-text-main placeholder-text-muted resize-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors min-h-[50px] max-h-[150px] overflow-y-auto shadow-sm"
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
            className="absolute right-2 bottom-1.5 rounded-lg p-2 h-auto w-auto"
            aria-label="Send"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </Button>
        </div>
      </footer>
    </div>
  );
}
