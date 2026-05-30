'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { apiBaseUrl } from '@/lib/api/client';
import { getStoredAccessToken } from '@/lib/auth/auth-store';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  transcript?: string | null;
  audioUrl?: string | null;
};

const API_URL = apiBaseUrl();

function authHeaders(extra?: HeadersInit): HeadersInit {
  const token = getStoredAccessToken();
  return {
    ...(extra || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function audioUrlFromPayload(audio: any): string | null {
  if (!audio) return null;
  if (audio.url) return audio.url;
  if (audio.base64) {
    return `data:${audio.contentType || audio.content_type || 'audio/wav'};base64,${audio.base64}`;
  }
  return null;
}

function mergeChunks(chunks: Float32Array[]) {
  const length = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const merged = new Float32Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }
  return merged;
}

function encodeWav(samples: Float32Array, sampleRate: number) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeString = (offset: number, value: string) => {
    for (let i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i));
  };
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);
  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }
  return new Blob([view], { type: 'audio/wav' });
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
  const [isSending, setIsSending] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const audioCtx = useRef<AudioContext | null>(null);
  const src = useRef<MediaStreamAudioSourceNode | null>(null);
  const proc = useRef<ScriptProcessorNode | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Float32Array[]>([]);
  const sampleRate = useRef(48000);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function addMessage(msg: ChatMessage) {
    setMessages((prev) => [...prev, msg]);
  }

  async function sendText() {
    const text = input.trim();
    if (!text || isSending) return;
    setInput('');
    setIsSending(true);
    addMessage({ id: crypto.randomUUID(), role: 'user', text });

    try {
      const res = await fetch(`${API_URL}/ai/chat/messages`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          conversationId,
          input: [{ type: 'text', text }],
          responseModalities: ['text'],
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setConversationId(data.conversationId);
      addMessage({
        id: data.assistantMessageId || crypto.randomUUID(),
        role: 'assistant',
        text: data.output?.text || 'Нет ответа',
        audioUrl: audioUrlFromPayload(data.output?.audio),
      });
    } catch (e: any) {
      addMessage({ id: crypto.randomUUID(), role: 'assistant', text: `Ошибка: ${e.message}` });
    } finally {
      setIsSending(false);
    }
  }

  async function startRecording() {
    const s = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ctx = new AudioContext();
    const source = ctx.createMediaStreamSource(s);
    const processor = ctx.createScriptProcessor(4096, 1, 1);
    chunks.current = [];
    sampleRate.current = ctx.sampleRate;
    processor.onaudioprocess = (e) => {
      chunks.current.push(new Float32Array(e.inputBuffer.getChannelData(0)));
    };
    source.connect(processor);
    processor.connect(ctx.destination);
    audioCtx.current = ctx;
    src.current = source;
    proc.current = processor;
    stream.current = s;
    setIsRecording(true);
  }

  async function stopRecording() {
    proc.current?.disconnect();
    src.current?.disconnect();
    stream.current?.getTracks().forEach((t) => t.stop());
    await audioCtx.current?.close();
    setIsRecording(false);
    const wav = encodeWav(mergeChunks(chunks.current), sampleRate.current);
    await sendAudio(wav);
  }

  async function sendAudio(blob: Blob) {
    setIsSending(true);
    const voiceMsgId = crypto.randomUUID();
    addMessage({ id: voiceMsgId, role: 'user', text: '🎤 Распознавание...' });

    const form = new FormData();
    form.append('audio', blob, 'voice.wav');
    form.append('audioFormat', 'wav');
    form.append('responseModalities', 'text,audio');
    if (conversationId) form.append('conversationId', conversationId);

    try {
      const res = await fetch(`${API_URL}/ai/chat/audio`, {
        method: 'POST',
        headers: authHeaders(),
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setConversationId(data.conversationId);

      const transcribedText = data.requestText || data.output?.transcript;

      if (transcribedText) {
        setMessages((prev) =>
          prev.map((m) => (m.id === voiceMsgId ? { ...m, text: transcribedText } : m))
        );
      }

      addMessage({
        id: data.assistantMessageId || crypto.randomUUID(),
        role: 'assistant',
        text: data.output?.text || 'Нет ответа',
        transcript: transcribedText,
        audioUrl: audioUrlFromPayload(data.output?.audio),
      });
    } catch (e: any) {
      setMessages((prev) =>
        prev.map((m) => (m.id === voiceMsgId ? { ...m, text: 'Ошибка распознавания' } : m))
      );
      addMessage({ id: crypto.randomUUID(), role: 'assistant', text: `Ошибка: ${e.message}` });
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <h1 className="text-3xl font-bold">Чат</h1>
        <Badge variant="secondary">Бета</Badge>
      </div>

      <Card className="h-[600px] flex flex-col">
        <CardHeader className="border-b">
          <CardTitle className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            Финансовый ассистент
          </CardTitle>
        </CardHeader>

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
                    {msg.audioUrl && (
                      <audio className="mt-2 w-full" controls autoPlay src={msg.audioUrl} />
                    )}
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
          <div ref={bottomRef} />
        </CardContent>

        <div className="border-t p-4">
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
              disabled={isSending}
            />
            <Button
              variant={isRecording ? 'destructive' : 'outline'}
              disabled={isSending}
              onClick={() => (isRecording ? stopRecording() : startRecording())}
            >
              {isRecording ? 'Стоп' : '🎤 Голос'}
            </Button>
            <Button onClick={sendText} disabled={isSending || !input.trim()}>
              Отправить
            </Button>
          </div>
        </div>
      </Card>

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
    </div>
  );
}
