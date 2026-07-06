"use client";

import { useEffect, useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Send, ShieldAlert, Sparkles } from "lucide-react";

export default function CompanionPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestedButtons, setSuggestedButtons] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/api/chat').then(r => r.json()).then(data => {
      setMessages(data);
      if (data.length > 0) {
        setSuggestedButtons(data[data.length - 1].suggested_buttons || []);
      }
    });
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, suggestedButtons]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMsg = { role: 'user', content: text, mode: 'normal' };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setSuggestedButtons([]);
    setLoading(true);

    const res = await fetch('/api/agent/turn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_type: 'chat', content: text }),
    });
    
    const data = await res.json();
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: data.assistant_response,
      mode: data.mode,
      safety_status: data.safety_status
    }]);
    setSuggestedButtons(data.suggested_buttons || []);
    setLoading(false);
  };

  const getModeColor = (mode: string, safety: string) => {
    if (safety === 'crisis' || safety === 'urgent') return "bg-red-100 text-red-800 border-red-200";
    if (mode === 'aftermath') return "bg-amber-50 text-amber-800 border-amber-200";
    if (mode === 'safety') return "bg-rose-50 text-rose-800 border-rose-200";
    return "bg-indigo-50 text-indigo-700 border-indigo-200";
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between pb-4 border-b">
        <h1 className="text-xl font-semibold flex items-center">
          <Sparkles className="w-5 h-5 mr-2 text-indigo-500" /> Companion
        </h1>
        {messages.length > 0 && messages[messages.length - 1]?.mode && (
          <Badge variant="outline" className={getModeColor(messages[messages.length - 1].mode, messages[messages.length - 1].safety_status)}>
            {messages[messages.length - 1].mode.replace('_', ' ').toUpperCase()} MODE
          </Badge>
        )}
      </div>

      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4 pb-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-10">
              Start a conversation. The companion is here to listen.
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-[15px] ${
                msg.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-br-none' 
                  : 'bg-white border border-gray-100 shadow-sm rounded-bl-none text-gray-800'
              }`}>
                {msg.content.split('\n').map((line: string, i: number) => (
                  <span key={i}>{line}<br/></span>
                ))}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-bl-none px-4 py-3 text-gray-500 flex gap-1">
                <span className="animate-bounce">.</span>
                <span className="animate-bounce delay-100">.</span>
                <span className="animate-bounce delay-200">.</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="pt-4 mt-auto">
        {suggestedButtons.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {suggestedButtons.map(btn => (
              <Button 
                key={btn} 
                variant="outline" 
                size="sm" 
                className="rounded-full bg-white text-indigo-700 border-indigo-200 hover:bg-indigo-50"
                onClick={() => handleSend(btn)}
              >
                {btn}
              </Button>
            ))}
          </div>
        )}
        <form onSubmit={(e) => { e.preventDefault(); handleSend(input); }} className="flex gap-2 relative">
          <Input 
            value={input} 
            onChange={e => setInput(e.target.value)} 
            placeholder="Type your message..." 
            className="rounded-full pl-4 pr-12 h-12 bg-white shadow-sm border-gray-200"
            disabled={loading}
          />
          <Button 
            type="submit" 
            size="icon" 
            className="absolute right-1 top-1 h-10 w-10 rounded-full bg-indigo-600 hover:bg-indigo-700"
            disabled={!input.trim() || loading}
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
