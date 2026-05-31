'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  useConversations,
  useConversation,
  useCreateConversation,
  useDeleteConversation,
} from '@/lib/api/queries/ai-chat';
import apiClient from '@/lib/api/client';
import { apiErrorMessage } from '@/lib/api/errors';
import { VoiceButton } from '@/components/chat/voice-button';
import { VoiceVisualizer } from '@/components/chat/voice-visualizer';
import type { AiChatConversation } from '@/lib/api/types';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  audioUrl?: string | null;
};

function messagesFromConversation(conv: AiChatConversation): ChatMessage[] {
  return conv.messages.map((msg) => {
    const textParts = msg.content
      .filter((p) => p.type === 'text' && p.text)
      .map((p) => p.text!)
      .join('\n');
    const hasAudio = msg.content.some((p) => p.type === 'audio');
    return {
      id: msg.id,
      role: msg.role as 'user' | 'assistant',
      text: textParts || (hasAudio ? '🎤 Голосовое сообщение' : ''),
    };
  });
}

function audioUrlFromPayload(audio: any): string | null {
  if (!audio) return null;
  if (audio.url) return audio.url;
  if (audio.base64) {
    return `data:${audio.contentType || audio.content_type || 'audio/wav'};base64,${audio.base64}`;
  }
  return null;
}

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  text: 'Здравствуйте! Я ваш финансовый ассистент. Могу ответить текстом или голосом. Чем помочь?',
};

export default function ChatPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [restartToken, setRestartToken] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const seamless = process.env.NEXT_PUBLIC_VOICE_AUTO_RESTART === 'true';

  const conversations = useConversations();
  const createConversation = useCreateConversation();
  const deleteConversation = useDeleteConversation();
  const conversationData = useConversation(selectedConversationId);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const voiceAudioRef = useRef<HTMLAudioElement>(null);
  const conversationIdRef = useRef<string | null>(selectedConversationId);
  conversationIdRef.current = selectedConversationId;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (conversationData.data) {
      const msgs = messagesFromConversation(conversationData.data);
      setMessages(msgs.length > 0 ? msgs : [WELCOME_MESSAGE]);
    }
  }, [conversationData.data]);

  const finishTurn = useCallback(() => {
    setBusy(false);
    if (seamless) setRestartToken((t) => t + 1);
  }, [seamless]);

  const playVoiceResponse = useCallback(
    (url: string) => {
      const audio = voiceAudioRef.current;
      if (!audio) {
        finishTurn();
        return;
      }
      const onEnded = () => {
        audio.removeEventListener('ended', onEnded);
        finishTurn();
      };
      const onError = () => {
        audio.removeEventListener('error', onError);
        finishTurn();
      };
      audio.addEventListener('ended', onEnded);
      audio.addEventListener('error', onError);
      audio.currentTime = 0;
      audio.src = url;
      audio.play().catch(() => finishTurn());
    },
    [finishTurn],
  );

  function addMessage(msg: ChatMessage) {
    setMessages((prev) => [...prev, msg]);
  }

  const handleNewChat = async () => {
    const result = await createConversation.mutateAsync(undefined);
    setSelectedConversationId(result.id);
    setMessages([]);
    setVoiceMode(false);
  };

  const handleSelectConversation = (id: string) => {
    setSelectedConversationId(id);
    setVoiceMode(false);
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await deleteConversation.mutateAsync(id);
    if (selectedConversationId === id) {
      setSelectedConversationId(null);
      setMessages([WELCOME_MESSAGE]);
    }
  };

  async function sendText() {
    const text = input.trim();
    if (!text || busy) return;
    setInput('');
    setBusy(true);
    addMessage({ id: crypto.randomUUID(), role: 'user', text });

    try {
      const body: Record<string, unknown> = {
        input: [{ type: 'text', text }],
        responseModalities: ['text'],
      };
      if (selectedConversationId) body.conversationId = selectedConversationId;

      const { data } = await apiClient.post('/ai/chat/messages', body, { timeout: 60000 });
      if (data.conversationId) {
        setSelectedConversationId(data.conversationId);
      }
      const audioUrl = audioUrlFromPayload(data.output?.audio);
      addMessage({
        id: data.assistantMessageId || crypto.randomUUID(),
        role: 'assistant',
        text: data.output?.text || 'Нет ответа',
        audioUrl,
      });
      if (audioUrl) {
        playVoiceResponse(audioUrl);
      } else {
        setBusy(false);
        conversations.refetch();
      }
    } catch (e: any) {
      addMessage({ id: crypto.randomUUID(), role: 'assistant', text: `Ошибка: ${apiErrorMessage(e, 'Ошибка')}` });
      setBusy(false);
    }
  }

  const handleVoiceAudio = useCallback(
    async (blob: Blob) => {
      setBusy(true);
      const cid = conversationIdRef.current;
      const voiceMsgId = crypto.randomUUID();
      addMessage({ id: voiceMsgId, role: 'user', text: '🎤 Распознавание...' });

      const form = new FormData();
      form.append('audio', blob, 'voice.wav');
      form.append('audioFormat', 'wav');
      form.append('responseModalities', 'text,audio');
      if (cid) form.append('conversationId', cid);

      try {
        const { data } = await apiClient.post('/ai/chat/audio', form, {
          timeout: 120000,
          transformRequest: [(d: any) => d],
        });
        if (data.conversationId) {
          setSelectedConversationId(data.conversationId);
        }

        const transcribedText = data.requestText || data.output?.transcript;
        const responseText = data.output?.text || 'Нет ответа';
        const audioUrl = audioUrlFromPayload(data.output?.audio);

        if (transcribedText) {
          setMessages((prev) =>
            prev.map((m) => (m.id === voiceMsgId ? { ...m, text: transcribedText } : m)),
          );
        }

        addMessage({
          id: data.assistantMessageId || crypto.randomUUID(),
          role: 'assistant',
          text: responseText,
          audioUrl,
        });

        if (audioUrl) {
          playVoiceResponse(audioUrl);
        } else {
          finishTurn();
          conversations.refetch();
        }
      } catch (e: any) {
        setMessages((prev) =>
          prev.map((m) => (m.id === voiceMsgId ? { ...m, text: 'Ошибка распознавания' } : m)),
        );
        addMessage({ id: crypto.randomUUID(), role: 'assistant', text: `Ошибка: ${apiErrorMessage(e, 'Ошибка')}` });
        finishTurn();
      }
    },
    [finishTurn, playVoiceResponse],
  );

  const sidebar = (
    <div className={`${sidebarOpen ? 'w-72' : 'w-0'} shrink-0 transition-all duration-200 overflow-hidden border-r bg-white flex flex-col`}>
      <div className="p-3 border-b">
        <Button
          className="w-full"
          onClick={handleNewChat}
          disabled={createConversation.isLoading}
        >
          {createConversation.isLoading ? 'Создаём...' : '+ Новый чат'}
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {conversations.isLoading && (
          <div className="p-4 text-sm text-gray-500">Загрузка...</div>
        )}
        {conversations.data?.items?.map((conv) => (
          <div
            key={conv.id}
            onClick={() => handleSelectConversation(conv.id)}
            className={`group flex items-center justify-between px-3 py-2.5 cursor-pointer hover:bg-gray-100 text-sm border-b border-gray-100 ${
              selectedConversationId === conv.id ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
            }`}
          >
            <div className="min-w-0 flex-1 mr-2">
              <div className="font-medium truncate">{conv.title || 'Новый диалог'}</div>
              {conv.lastMessagePreview && (
                <div className="text-xs text-gray-500 truncate">{conv.lastMessagePreview}</div>
              )}
            </div>
            <button
              onClick={(e) => handleDeleteConversation(conv.id, e)}
              className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 shrink-0 p-0.5"
              title="Удалить"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
            </button>
          </div>
        ))}
        {!conversations.isLoading && conversations.data?.items?.length === 0 && (
          <div className="p-4 text-sm text-gray-400">Нет диалогов</div>
        )}
        {conversations.isError && (
          <div className="p-4 text-sm text-red-500">Ошибка загрузки</div>
        )}
      </div>
    </div>
  );

  const messageList = (
    <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[82%] rounded-lg p-4 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-none'
                : 'bg-gray-100 text-gray-950 rounded-bl-none'
            }`}
          >
            <div className="flex items-start gap-2">
              {msg.role === 'assistant' && (
                <Avatar className="w-6 h-6">
                  <AvatarFallback className="text-xs">ФА</AvatarFallback>
                </Avatar>
              )}
              <div className="min-w-0">
                <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
              </div>
              {msg.role === 'user' && (
                <Avatar className="w-6 h-6">
                  <AvatarFallback className="text-xs">Я</AvatarFallback>
                </Avatar>
              )}
            </div>
          </div>
        </div>
      ))}
      {busy && (
        <div className="flex justify-start">
          <div className="bg-gray-100 rounded-lg rounded-bl-none p-4">
            <div className="flex items-center gap-3">
              <VoiceVisualizer state="processing" size={28} />
              <span className="text-sm text-muted-foreground">Ассистент отвечает...</span>
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </CardContent>
  );

  const inputArea = (
    <div className="border-t p-4 shrink-0">
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Введите сообщение..."
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendText();
            }
          }}
          disabled={busy}
        />
        <Button onClick={sendText} disabled={busy || !input.trim()}>
          Отправить
        </Button>
        <Button
          variant="outline"
          onClick={() => setVoiceMode(true)}
          disabled={busy}
        >
          🎤 Голос
        </Button>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
          </Button>
          <h1 className="text-3xl font-bold">Чат</h1>
        </div>
        <Badge variant="secondary">Бета</Badge>
      </div>

      <div className="flex h-[600px]">
        {sidebar}
        <Card className="flex-1 flex flex-col rounded-l-none border-l-0">
          <CardHeader className="border-b shrink-0 py-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              {conversationData.data?.title || 'Финансовый ассистент'}
            </CardTitle>
          </CardHeader>

          {voiceMode ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-6 p-6">
              <VoiceButton
                onAudioReady={handleVoiceAudio}
                disabled={busy}
                processing={busy}
                size={200}
                seamless={seamless}
                restartToken={restartToken}
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setVoiceMode(false)}
                disabled={busy}
              >
                Текстовый ввод
              </Button>
            </div>
          ) : (
            <>
              {messageList}
              {inputArea}
            </>
          )}
        </Card>
      </div>

      <audio ref={voiceAudioRef} className="sr-only" />

      {!voiceMode && (
        <Card>
          <CardHeader>
            <CardTitle>Быстрые действия</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto py-4" onClick={() => { setInput('Проанализируй мои расходы'); }}>
              <div className="text-left">
                <p className="font-medium">Анализ расходов</p>
                <p className="text-sm text-muted-foreground">Разбор трат по категориям</p>
              </div>
            </Button>
            <Button variant="outline" className="h-auto py-4" onClick={() => { setInput('Помоги спланировать накопления'); }}>
              <div className="text-left">
                <p className="font-medium">План накоплений</p>
                <p className="text-sm text-muted-foreground">Стратегия сбережений</p>
              </div>
            </Button>
            <Button variant="outline" className="h-auto py-4" onClick={() => { setInput('Проверь мой бюджет'); }}>
              <div className="text-left">
                <p className="font-medium">Проверка бюджета</p>
                <p className="text-sm text-muted-foreground">План против факта</p>
              </div>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
