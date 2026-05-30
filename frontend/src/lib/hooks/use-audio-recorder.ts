'use client';

import { useRef, useState, useCallback, useEffect } from 'react';

interface UseAudioRecorderOptions {
  silenceThreshold?: number;
  silenceDurationMs?: number;
  onSilence?: () => void;
}

interface UseAudioRecorderReturn {
  isRecording: boolean;
  isSupported: boolean;
  error: string | null;
  amplitude: number;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob>;
}

const DEFAULT_SILENCE_THRESHOLD = parseFloat(
  process.env.NEXT_PUBLIC_VOICE_SILENCE_THRESHOLD || '0.08',
);
const DEFAULT_SILENCE_DURATION_MS = parseInt(
  process.env.NEXT_PUBLIC_VOICE_SILENCE_DURATION_MS || '1500',
  10,
);

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

export function useAudioRecorder(options: UseAudioRecorderOptions = {}): UseAudioRecorderReturn {
  const {
    silenceThreshold = DEFAULT_SILENCE_THRESHOLD,
    silenceDurationMs = DEFAULT_SILENCE_DURATION_MS,
    onSilence,
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [amplitude, setAmplitude] = useState(0);

  const audioCtx = useRef<AudioContext | null>(null);
  const source = useRef<MediaStreamAudioSourceNode | null>(null);
  const processor = useRef<ScriptProcessorNode | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Float32Array[]>([]);
  const sampleRate = useRef(48000);
  const latestAmplitude = useRef(0);
  const silenceMs = useRef(0);
  const silenceFired = useRef(false);
  const onSilenceRef = useRef(onSilence);
  onSilenceRef.current = onSilence;

  const isSupported =
    typeof window !== 'undefined' &&
    typeof navigator !== 'undefined' &&
    !!navigator.mediaDevices?.getUserMedia;

  useEffect(() => {
    if (!isRecording) {
      setAmplitude(0);
      return;
    }
    let raf: number;
    const tick = () => {
      setAmplitude(latestAmplitude.current);
      if (silenceFired.current) {
        silenceFired.current = false;
        onSilenceRef.current?.();
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [isRecording]);

  const cleanup = useCallback(() => {
    processor.current?.disconnect();
    source.current?.disconnect();
    stream.current?.getTracks().forEach((t) => t.stop());
    audioCtx.current?.close();
    audioCtx.current = null;
    source.current = null;
    processor.current = null;
    stream.current = null;
  }, []);

  const startRecording = useCallback(async () => {
    setError(null);
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new AudioContext();
      const src = ctx.createMediaStreamSource(s);
      const proc = ctx.createScriptProcessor(4096, 1, 1);
      chunks.current = [];
      sampleRate.current = ctx.sampleRate;
      latestAmplitude.current = 0;
      silenceMs.current = 0;
      silenceFired.current = false;
      proc.onaudioprocess = (e) => {
        const data = e.inputBuffer.getChannelData(0);
        chunks.current.push(new Float32Array(data));
        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
        const rms = Math.sqrt(sum / data.length);
        latestAmplitude.current = Math.min(1, rms * 5);
        const chunkDurationMs = (data.length / ctx.sampleRate) * 1000;
        if (latestAmplitude.current < silenceThreshold) {
          silenceMs.current += chunkDurationMs;
          if (silenceMs.current >= silenceDurationMs && !silenceFired.current) {
            silenceFired.current = true;
          }
        } else {
          silenceMs.current = 0;
        }
      };
      src.connect(proc);
      proc.connect(ctx.destination);
      audioCtx.current = ctx;
      source.current = src;
      processor.current = proc;
      stream.current = s;
      setIsRecording(true);
    } catch (e: any) {
      setError(e.message || 'Не удалось получить доступ к микрофону');
    }
  }, [silenceThreshold, silenceDurationMs]);

  const stopRecording = useCallback(async (): Promise<Blob> => {
    silenceFired.current = false;
    cleanup();
    setIsRecording(false);
    latestAmplitude.current = 0;
    return encodeWav(mergeChunks(chunks.current), sampleRate.current);
  }, [cleanup]);

  return { isRecording, isSupported, error, amplitude, startRecording, stopRecording };
}
