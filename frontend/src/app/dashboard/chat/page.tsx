'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import apiClient from '@/lib/api/client';
import { apiErrorMessage } from '@/lib/api/errors';
import { VoiceButton } from '@/components/chat/voice-button';
import { VoiceVisualizer } from '@/components/chat/voice-visualizer';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  transcript?: string | null;
  audioUrl?: string | null;
};

function audioUrlFromPayload(audio: any): string | null {
  if (!audio) return null;
  if (audio.url) return audio.url;
  if (audio.base64) {
    return `data:${audio.contentType || audio.content_type || 'audio/wav'};base64,${audio.base64}`;
  }
  return null;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Здравствуйте! Я ваш финансовый ассистент. Могу ответить текстом или голосом. Чем помочь?',
    },
  ]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [restartToken, setRestartToken] = useState(0);

  const seamless = process.env.NEXT_PUBLIC_VOICE_AUTO_RESTART === 'true';

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const voiceAudioRef = useRef<HTMLAudioElement>(null);
  const conversationIdRef = useRef(conversationId);
  conversationIdRef.current = conversationId;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
      if (conversationId) body.conversationId = conversationId;

      const { data } = await apiClient.post('/ai/chat/messages', body, { timeout: 60000 });
      setConversationId(data.conversationId);
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
          transformRequest: [(d) => d],
        });
        setConversationId(data.conversationId);

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
          transcript: transcribedText,
          audioUrl,
        });

        if (audioUrl) {
          playVoiceResponse(audioUrl);
        } else {
          finishTurn();
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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <h1 className="text-3xl font-bold">Чат</h1>
        <Badge variant="secondary">Бета</Badge>
      </div>

      <Card className="h-[600px] flex flex-col">
        <CardHeader className="border-b shrink-0">
          <CardTitle className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            Финансовый ассистент
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
          </>
        )}
      </Card>

      <audio ref={voiceAudioRef} className="sr-only" />

      {!voiceMode && (
        <Card>
          <CardHeader>
            <CardTitle>Быстрые действия</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto py-4">
              <div className="text-left">
                <p className="font-medium">Анализ расходов</p>
                <p className="text-sm text-muted-foreground">Разбор трат по категориям</p>
              </div>
            </Button>
            <Button variant="outline" className="h-auto py-4">
              <div className="text-left">
                <p className="font-medium">План накоплений</p>
                <p className="text-sm text-muted-foreground">Стратегия сбережений</p>
              </div>
            </Button>
            <Button variant="outline" className="h-auto py-4">
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
