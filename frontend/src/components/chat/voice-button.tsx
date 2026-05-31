'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { VoiceVisualizer } from './voice-visualizer';
import { useAudioRecorder } from '@/lib/hooks/use-audio-recorder';

interface VoiceButtonProps {
  onAudioReady: (blob: Blob) => void;
  disabled?: boolean;
  processing?: boolean;
  size?: number;
  seamless?: boolean;
  restartToken?: number;
}

export function VoiceButton({
  onAudioReady,
  disabled = false,
  processing = false,
  size = 48,
  seamless = false,
  restartToken = 0,
}: VoiceButtonProps) {
  const prevRestartToken = useRef(-1);
  const onAudioReadyRef = useRef(onAudioReady);
  onAudioReadyRef.current = onAudioReady;

  const handleSilence = useCallback(() => {
    if (!recordingRef.current) return;
    recordingRef.current = false;
    stopRecording().then((blob) => {
      if (blob.size > 0) onAudioReadyRef.current(blob);
    });
  }, []);

  const { isRecording, isSupported, amplitude, startRecording, stopRecording } =
    useAudioRecorder(seamless ? { onSilence: handleSilence } : {});

  const recordingRef = useRef(false);
  recordingRef.current = isRecording;

  const handleToggle = useCallback(async () => {
    if (disabled || processing) return;
    if (isRecording) {
      const blob = await stopRecording();
      onAudioReadyRef.current(blob);
    } else {
      await startRecording();
    }
  }, [disabled, processing, isRecording, startRecording, stopRecording]);

  useEffect(() => {
    if (!isSupported || !seamless) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === ' ' && !e.repeat && !disabled && !processing) {
        e.preventDefault();
        handleToggle();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isSupported, seamless, disabled, processing, handleToggle]);

  useEffect(() => {
    if (!seamless) return;
    if (restartToken !== prevRestartToken.current && !isRecording && !processing) {
      prevRestartToken.current = restartToken;
      startRecording();
    }
  }, [seamless, restartToken, isRecording, processing, startRecording]);

  useEffect(() => {
    prevRestartToken.current = restartToken;
  }, [restartToken]);

  const visualizerState = processing ? 'processing' : isRecording ? 'listening' : 'idle';

  if (!isSupported) {
    return null;
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="text-center text-sm text-muted-foreground">
        {isRecording
          ? seamless
            ? 'Говорите...'
            : 'Запись... Нажмите для остановки'
          : processing
            ? 'Обработка...'
            : seamless
              ? 'Слушаю...'
              : 'Нажмите для записи'}
      </div>
      <button
        type="button"
        className="relative focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed select-none cursor-pointer"
        style={{ width: size + 16, height: size + 16 }}
        onClick={handleToggle}
        disabled={disabled}
        aria-label={isRecording ? 'Остановить запись' : 'Начать запись голоса'}
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <VoiceVisualizer state={visualizerState} size={size} amplitude={amplitude} />
        </div>
      </button>
    </div>
  );
}
