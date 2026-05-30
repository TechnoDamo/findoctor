"use client";

import Link from "next/link";
import { CSSProperties, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { FinanceHeader } from "@/components/FinanceHeader";
import { sendConsultantAudioMessage } from "@/lib/consultantApi";
import { useConsultantChatStore } from "@/lib/consultantChatStore";
import { consultantConfig } from "@/lib/consultantConfig";
import { financeRoutes } from "@/lib/financeRoutes";
import { useAudioRecorder } from "@/lib/hooks/useAudioRecorder";

import styles from "./consultant-audio-page.module.css";

type VoiceMode = "idle" | "recording" | "waiting" | "playing";

type PlaybackNodes = {
  context: AudioContext;
  analyser: AnalyserNode;
  source: MediaElementAudioSourceNode;
  waveform: Uint8Array<ArrayBuffer>;
  rafId: number;
};

function getStatusText(mode: VoiceMode): string {
  if (mode === "recording") {
    return "Слушаю вас...";
  }

  if (mode === "waiting") {
    return "Обрабатываю запрос...";
  }

  if (mode === "playing") {
    return "Проигрываю ответ...";
  }

  return "Нажмите на сферу и говорите";
}

export function ConsultantAudioPage() {
  const [mode, setMode] = useState<VoiceMode>("idle");
  const [playbackAmplitude, setPlaybackAmplitude] = useState(0);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [silenceSignal, setSilenceSignal] = useState(0);

  const { state, appendMessage, updateMessage, setConversationId } = useConsultantChatStore();

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playbackNodesRef = useRef<PlaybackNodes | null>(null);
  const isSubmittingRef = useRef(false);

  const stopPlaybackMonitor = useCallback(() => {
    const playbackNodes = playbackNodesRef.current;

    if (!playbackNodes) {
      return;
    }

    window.cancelAnimationFrame(playbackNodes.rafId);
    playbackNodes.rafId = 0;
    setPlaybackAmplitude(0);
  }, []);

  const ensurePlaybackNodes = useCallback((): PlaybackNodes | null => {
    const audioElement = audioRef.current;

    if (!audioElement) {
      return null;
    }

    if (playbackNodesRef.current) {
      return playbackNodesRef.current;
    }

    const context = new AudioContext();
    const analyser = context.createAnalyser();
    analyser.fftSize = consultantConfig.playback.analyserFftSize;
    const source = context.createMediaElementSource(audioElement);

    source.connect(analyser);
    analyser.connect(context.destination);

    const waveform = new Uint8Array(new ArrayBuffer(analyser.fftSize));

    playbackNodesRef.current = {
      context,
      analyser,
      source,
      waveform,
      rafId: 0,
    };

    return playbackNodesRef.current;
  }, []);

  const startPlaybackMonitor = useCallback(() => {
    const playbackNodes = ensurePlaybackNodes();

    if (!playbackNodes) {
      return;
    }

    const tick = () => {
      playbackNodes.analyser.getByteTimeDomainData(playbackNodes.waveform);

      let sum = 0;

      for (let index = 0; index < playbackNodes.waveform.length; index += 1) {
        const normalized = (playbackNodes.waveform[index] - 128) / 128;
        sum += normalized * normalized;
      }

      const rms = Math.sqrt(sum / playbackNodes.waveform.length);
      const floor = consultantConfig.playback.idleFloor;
      const target = Math.min(1, Math.max(floor, rms * 4));
      const smoothing = consultantConfig.playback.amplitudeSmoothing;

      setPlaybackAmplitude((previous) => previous + (target - previous) * smoothing);

      playbackNodes.rafId = window.requestAnimationFrame(tick);
    };

    tick();
  }, [ensurePlaybackNodes]);

  const playAssistantAudio = useCallback(
    async (audioUrl: string) => {
      const audioElement = audioRef.current;

      if (!audioElement) {
        setMode("idle");
        return;
      }

      try {
        const playbackNodes = ensurePlaybackNodes();

        if (playbackNodes && playbackNodes.context.state !== "running") {
          await playbackNodes.context.resume();
        }
      } catch {
        setMode("idle");
        return;
      }

      const finishPlayback = () => {
        audioElement.removeEventListener("ended", finishPlayback);
        audioElement.removeEventListener("error", finishPlayback);
        stopPlaybackMonitor();
        setMode("idle");
      };

      audioElement.addEventListener("ended", finishPlayback);
      audioElement.addEventListener("error", finishPlayback);

      audioElement.src = audioUrl;
      audioElement.currentTime = 0;
      setMode("playing");
      startPlaybackMonitor();

      try {
        await audioElement.play();
      } catch {
        finishPlayback();
      }
    },
    [ensurePlaybackNodes, startPlaybackMonitor, stopPlaybackMonitor],
  );

  const submitVoiceMessage = useCallback(
    async (audioBlob: Blob) => {
      if (audioBlob.size < consultantConfig.recorder.minimumBlobBytes) {
        setMode("idle");
        return;
      }

      const pendingMessageId = crypto.randomUUID();

      appendMessage({
        id: pendingMessageId,
        role: "user",
        source: "voice",
        text: "Распознаю голосовой запрос...",
        createdAt: new Date().toISOString(),
      });

      setMode("waiting");
      setErrorText(null);
      isSubmittingRef.current = true;

      try {
        const response = await sendConsultantAudioMessage(audioBlob, state.conversationId);

        if (response.conversationId) {
          setConversationId(response.conversationId);
        }

        const userText = response.requestText ?? response.transcript ?? "Голосовой запрос";

        updateMessage(pendingMessageId, {
          text: userText,
        });

        appendMessage({
          id: response.assistantMessageId,
          role: "assistant",
          source: "voice",
          text: response.responseText,
          audioUrl: response.audioUrl,
          transcript: response.transcript,
          createdAt: new Date().toISOString(),
        });

        if (response.audioUrl) {
          await playAssistantAudio(response.audioUrl);
        } else {
          setMode("idle");
        }
      } catch (caughtError) {
        const fallbackMessage = caughtError instanceof Error ? caughtError.message : "Ошибка обработки голоса";

        updateMessage(pendingMessageId, {
          text: "Голосовой запрос не распознан",
        });

        appendMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          source: "voice",
          text: `Не удалось получить ответ: ${fallbackMessage}`,
          createdAt: new Date().toISOString(),
        });

        setErrorText(fallbackMessage);
        setMode("idle");
      } finally {
        isSubmittingRef.current = false;
      }
    },
    [appendMessage, playAssistantAudio, setConversationId, state.conversationId, updateMessage],
  );

  const handleSilenceDetected = useCallback(() => {
    setSilenceSignal((previous) => previous + 1);
  }, []);

  const recorder = useAudioRecorder({ onSilence: handleSilenceDetected });

  const { amplitude: recordingAmplitude, error: recorderError, isRecording, isSupported, startRecording, stopRecording } = recorder;

  useEffect(() => {
    if (silenceSignal === 0 || !isRecording || isSubmittingRef.current) {
      return;
    }

    let cancelled = false;

    const stopBySilence = async () => {
      const blob = await stopRecording();

      if (!cancelled) {
        await submitVoiceMessage(blob);
      }
    };

    void stopBySilence();

    return () => {
      cancelled = true;
    };
  }, [isRecording, silenceSignal, stopRecording, submitVoiceMessage]);

  useEffect(() => {
    return () => {
      stopPlaybackMonitor();

      if (playbackNodesRef.current) {
        playbackNodesRef.current.source.disconnect();
        playbackNodesRef.current.analyser.disconnect();
        void playbackNodesRef.current.context.close();
      }
    };
  }, [stopPlaybackMonitor]);

  const handleSphereClick = useCallback(async () => {
    if (mode === "waiting") {
      return;
    }

    setErrorText(null);

    if (isRecording) {
      const blob = await stopRecording();
      await submitVoiceMessage(blob);
      return;
    }

    if (mode === "playing") {
      const audioElement = audioRef.current;

      if (audioElement) {
        audioElement.pause();
      }

      stopPlaybackMonitor();
      setMode("idle");
      return;
    }

    setMode("recording");

    try {
      await startRecording();
    } catch {
      setMode("idle");
    }
  }, [isRecording, mode, startRecording, stopPlaybackMonitor, stopRecording, submitVoiceMessage]);

  const activeAmplitude = mode === "recording" ? recordingAmplitude : mode === "playing" ? playbackAmplitude : 0;
  const scaleDelta = consultantConfig.sphere.maxScale - consultantConfig.sphere.minScale;
  const liveScale = consultantConfig.sphere.minScale + activeAmplitude * scaleDelta;

  const pageStyle = useMemo(
    () =>
      ({
        "--voice-sphere-size": `${consultantConfig.sphere.sizePx}px`,
        "--voice-sphere-inner-inset": `${consultantConfig.sphere.innerInsetPx}px`,
        "--voice-sphere-live-scale": `${liveScale}`,
        "--voice-sphere-record-duration": `${consultantConfig.sphere.recordPulseDurationMs}ms`,
        "--voice-sphere-waiting-duration": `${consultantConfig.sphere.waitingPulseDurationMs}ms`,
        "--voice-sphere-playing-duration": `${consultantConfig.sphere.playingPulseDurationMs}ms`,
        "--voice-sphere-idle-duration": `${consultantConfig.sphere.idlePulseDurationMs}ms`,
        "--voice-sphere-morph-duration": `${consultantConfig.sphere.morphDurationMs}ms`,
        "--voice-sphere-wave-duration": `${consultantConfig.sphere.waveDurationMs}ms`,
        "--voice-sphere-wave-delay": `${consultantConfig.sphere.waveDelayMs}ms`,
        "--voice-sphere-scale-transition": `${consultantConfig.sphere.scaleTransitionMs}ms`,
      }) as CSSProperties,
    [liveScale],
  );

  const sphereClassName =
    mode === "recording"
      ? `${styles.voiceSphere} ${styles.recording}`
      : mode === "waiting"
        ? `${styles.voiceSphere} ${styles.waiting}`
        : mode === "playing"
          ? `${styles.voiceSphere} ${styles.playing}`
          : `${styles.voiceSphere} ${styles.idle}`;

  const statusText = getStatusText(mode);
  const helpText = recorderError ?? errorText;

  return (
    <main className={styles.page} style={pageStyle}>
      <div className={styles.content}>
        <section className={styles.headerZone}>
          <FinanceHeader
            title={"Мой\nконсультант"}
            leftHref={financeRoutes.consultant}
            leftIcon="back"
            prizeHref={financeRoutes.achievements}
            logoutHref="/login"
            titleClassName={styles.headerTitle}
          />
        </section>

        <section className={styles.voiceArea}>
          <h2 className={styles.voiceTitle}>{statusText}</h2>

          <button
            type="button"
            className={sphereClassName}
            onClick={handleSphereClick}
            aria-label={isRecording ? "Остановить запись и отправить" : "Запустить запись"}
            aria-pressed={isRecording}
            disabled={!isSupported || mode === "waiting"}
          >
            <span className={styles.voiceSphereInner} aria-hidden="true" />
          </button>

          <p className={styles.stateHint}>
            {mode === "recording" && "Остановлю запись сам, когда вы перестанете говорить."}
            {mode === "waiting" && "Подождите немного, формирую ответ."}
            {mode === "playing" && "Нажмите на сферу, чтобы остановить воспроизведение."}
            {mode === "idle" && "Нажмите, чтобы начать запись. Повторное нажатие отправит запрос."}
          </p>

          {helpText && <p className={styles.errorText}>{helpText}</p>}
          {!isSupported && <p className={styles.errorText}>В этом браузере недоступен доступ к микрофону.</p>}
        </section>

        <Link className={styles.backToChatButton} href={financeRoutes.consultant}>
          Вернуться в чат
        </Link>
      </div>

      <audio ref={audioRef} className={styles.hiddenAudio} />
    </main>
  );
}
