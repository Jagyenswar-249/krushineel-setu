import React, { useState } from 'react';
import { Language } from '../types';
import { translations } from '../i18n/translations';
import { X, Send, Smartphone, ShieldAlert, TrendingUp, Fish, CloudRain, LifeBuoy } from 'lucide-react';
import { api } from '../services/api';

interface SMSConsoleModalProps {
  isOpen: boolean;
  onClose: () => void;
  language: Language;
}

interface Message {
  id: string;
  sender: 'user' | 'system';
  text: string;
  time: string;
}

export const SMSConsoleModal: React.FC<SMSConsoleModalProps> = ({
  isOpen,
  onClose,
  language
}) => {
  if (!isOpen) return null;

  const t = translations[language];
  const [phoneNumber, setPhoneNumber] = useState('9876543211');
  const [inputText, setInputText] = useState('SAFE OD-02-MM-104');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm1',
      sender: 'system',
      text: 'KrushiNeel Setu SMS Gateway: Available commands: SAFE, TRIP, HELP, PRICE, SELL, WEATHER.',
      time: '10:00'
    }
  ]);

  const handleSend = async (customText?: string) => {
    const textToSend = customText || inputText;
    if (!textToSend.trim() || loading) return;

    const userMsg: Message = {
      id: `u_${Date.now()}`,
      sender: 'user',
      text: textToSend,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const res = await api.simulateSMS(textToSend, phoneNumber);
      const replyMsg: Message = {
        id: `s_${Date.now()}`,
        sender: 'system',
        text: res.response_sms,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, replyMsg]);
    } catch (e) {
      const errMsg: Message = {
        id: `err_${Date.now()}`,
        sender: 'system',
        text: 'Error contacting KrushiNeel SMS gateway. Please check backend connection.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Phone Notch & Header */}
        <div className="bg-slate-800 px-4 py-3 border-b border-slate-700 flex items-center justify-between text-slate-100">
          <div className="flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-teal-400" />
            <div>
              <h3 className="font-bold text-sm tracking-tight">{t.smsModal.title}</h3>
              <p className="text-[10px] text-slate-400">From: +91 {phoneNumber}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Shortcuts Bar */}
        <div className="bg-slate-800/60 p-2.5 border-b border-slate-700">
          <p className="text-[11px] font-semibold text-slate-300 mb-1.5 flex items-center gap-1">
            <span>{t.smsModal.shortcuts}</span>
          </p>
          <div className="grid grid-cols-2 gap-1.5 text-xs">
            <button
              onClick={() => handleSend('SAFE OD-02-MM-104')}
              className="bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-1.5 rounded text-left truncate hover:bg-emerald-900 font-mono text-[11px]"
            >
              SAFE (Boat Check-in)
            </button>
            <button
              onClick={() => handleSend('HELP OD-02-MM-104')}
              className="bg-rose-950 text-rose-300 border border-rose-800 px-2 py-1.5 rounded text-left truncate hover:bg-rose-900 font-mono text-[11px]"
            >
              HELP (SOS Distress)
            </button>
            <button
              onClick={() => handleSend('PRICE TOMATO BBSR')}
              className="bg-amber-950 text-amber-300 border border-amber-800 px-2 py-1.5 rounded text-left truncate hover:bg-amber-900 font-mono text-[11px]"
            >
              PRICE TOMATO BBSR
            </button>
            <button
              onClick={() => handleSend('WEATHER PURI')}
              className="bg-cyan-950 text-cyan-300 border border-cyan-800 px-2 py-1.5 rounded text-left truncate hover:bg-cyan-900 font-mono text-[11px]"
            >
              WEATHER PURI
            </button>
            <button
              onClick={() => handleSend('SELL HILSA 40 500 PURI')}
              className="bg-blue-950 text-blue-300 border border-blue-800 px-2 py-1.5 rounded text-left truncate hover:bg-blue-900 font-mono text-[11px]"
            >
              SELL HILSA 40 500 PURI
            </button>
            <button
              onClick={() => handleSend('TRIP OD-02-MM-104 12')}
              className="bg-purple-950 text-purple-300 border border-purple-800 px-2 py-1.5 rounded text-left truncate hover:bg-purple-900 font-mono text-[11px]"
            >
              TRIP OD-02-MM-104 12
            </button>
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-950 font-sans text-xs min-h-[220px]">
          {messages.map((m) => {
            const isUser = m.sender === 'user';
            return (
              <div
                key={m.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 shadow-md ${
                    isUser
                      ? 'bg-emerald-600 text-white rounded-br-none'
                      : 'bg-slate-800 text-slate-100 border border-slate-700 rounded-bl-none'
                  }`}
                >
                  <p className="leading-relaxed whitespace-pre-wrap">{m.text}</p>
                </div>
                <span className="text-[10px] text-slate-500 mt-1 px-1">
                  {m.time}
                </span>
              </div>
            );
          })}
          {loading && (
            <div className="flex items-center gap-1.5 text-slate-400 text-xs italic">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-100"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-200"></span>
              <span>Processing via KrushiNeel SMS Parser...</span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-3 bg-slate-900 border-t border-slate-800 flex items-center gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={t.smsModal.placeholder}
            className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !inputText.trim()}
            className="bg-primary hover:bg-teal-700 text-white p-2.5 rounded-xl transition-colors disabled:opacity-50"
            title={t.smsModal.sendBtn}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
