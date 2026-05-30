"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { consultantConfig } from "@/lib/consultantConfig";

type UseAudioRecorderOptions = {
  onSilence?: () => void;
};

type UseAudioRecorderResult = {
  isRecording: boolean;
  isSupported: boolean;
  amplitude: number;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob>;
};

function mergeChunks(chunks: Float32Array[]): Float32Array {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const merged = new Float32Array(totalLength);

  let offset = 0;

  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }

  return merged;
}

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeString = (offset: number, value: string) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;

  for (let index = 0; index < samples.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, samples[index]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    offset += 2;
  }

  return new Blob([view], { type: "audio/wav" });
}

export function useAudioRecorder(options: UseAudioRecorderOptions = {}): UseAudioRecorderResult {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [amplitude, setAmplitude] = useState(0);

  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sampleRateRef = useRef(48_000);
  const chunksRef = useRef<Float32Array[]>([]);
  const silenceMsRef = useRef(0);
  const silenceFiredRef = useRef(false);
  const amplitudeRef = useRef(0);
  const onSilenceRef = useRef(options.onSilence);

  useEffect(() => {
    onSilenceRef.current = options.onSilence;
  }, [options.onSilence]);

  const isSupported =
    typeof window !== "undefined" &&
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function";

  useEffect(() => {
    if (!isRecording) {
      return;
    }

    let animationFrameId = 0;

    const updateAmplitude = () => {
      setAmplitude(amplitudeRef.current);

      if (silenceFiredRef.current) {
        silenceFiredRef.current = false;
        onSilenceRef.current?.();
      }

      animationFrameId = window.requestAnimationFrame(updateAmplitude);
    };

    animationFrameId = window.requestAnimationFrame(updateAmplitude);

    return () => {
      window.cancelAnimationFrame(animationFrameId);
    };
  }, [isRecording]);

  const cleanup = useCallback(() => {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((track) => track.stop());

    if (audioContextRef.current) {
      void audioContextRef.current.close();
    }

    processorRef.current = null;
    sourceRef.current = null;
    streamRef.current = null;
    audioContextRef.current = null;
  }, []);

  const startRecording = useCallback(async () => {
    setError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(
        consultantConfig.recorder.processorBufferSize,
        1,
        1,
      );

      chunksRef.current = [];
      sampleRateRef.current = audioContext.sampleRate;
      silenceMsRef.current = 0;
      silenceFiredRef.current = false;
      amplitudeRef.current = 0;

      processor.onaudioprocess = (event) => {
        const channelData = event.inputBuffer.getChannelData(0);
        chunksRef.current.push(new Float32Array(channelData));

        let sum = 0;

        for (let index = 0; index < channelData.length; index += 1) {
          sum += channelData[index] * channelData[index];
        }

        const rms = Math.sqrt(sum / channelData.length);
        const targetAmplitude = Math.min(1, rms * consultantConfig.recorder.amplitudeMultiplier);
        const smoothing = consultantConfig.recorder.amplitudeSmoothing;

        amplitudeRef.current += (targetAmplitude - amplitudeRef.current) * smoothing;

        const chunkDurationMs = (channelData.length / audioContext.sampleRate) * 1000;

        if (amplitudeRef.current < consultantConfig.recorder.silenceThreshold) {
          silenceMsRef.current += chunkDurationMs;

          if (
            silenceMsRef.current >= consultantConfig.recorder.silenceDurationMs &&
            !silenceFiredRef.current
          ) {
            silenceFiredRef.current = true;
          }
        } else {
          silenceMsRef.current = 0;
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      audioContextRef.current = audioContext;
      sourceRef.current = source;
      processorRef.current = processor;
      streamRef.current = stream;

      setIsRecording(true);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Не удалось включить микрофон";
      setError(message);
      throw new Error(message);
    }
  }, []);

  const stopRecording = useCallback(async () => {
    silenceFiredRef.current = false;
    cleanup();
    setIsRecording(false);
    amplitudeRef.current = 0;

    return encodeWav(mergeChunks(chunksRef.current), sampleRateRef.current);
  }, [cleanup]);

  return {
    isRecording,
    isSupported,
    amplitude,
    error,
    startRecording,
    stopRecording,
  };
}
