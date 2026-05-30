function getNumberEnv(name: string, fallback: number): number {
  const value = process.env[name];

  if (typeof value !== "string") {
    return fallback;
  }

  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return parsed;
}

function getPositiveNumberEnv(name: string, fallback: number): number {
  const parsed = getNumberEnv(name, fallback);

  if (parsed <= 0) {
    return fallback;
  }

  return parsed;
}

export const consultantConfig = {
  storage: {
    maxMessages: getPositiveNumberEnv("NEXT_PUBLIC_CONSULTANT_MAX_MESSAGES", 120),
  },
  network: {
    textTimeoutMs: getPositiveNumberEnv("NEXT_PUBLIC_CONSULTANT_TEXT_TIMEOUT_MS", 60_000),
    audioTimeoutMs: getPositiveNumberEnv("NEXT_PUBLIC_CONSULTANT_AUDIO_TIMEOUT_MS", 120_000),
  },
  recorder: {
    silenceThreshold: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SILENCE_THRESHOLD", 0.08),
    silenceDurationMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SILENCE_DURATION_MS", 1_300),
    processorBufferSize: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_PROCESSOR_BUFFER_SIZE", 4096),
    amplitudeMultiplier: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_AMPLITUDE_MULTIPLIER", 5),
    amplitudeSmoothing: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_AMPLITUDE_SMOOTHING", 0.2),
    minimumBlobBytes: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_MIN_BLOB_BYTES", 900),
  },
  playback: {
    analyserFftSize: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_PLAYBACK_FFT_SIZE", 2048),
    amplitudeSmoothing: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_PLAYBACK_SMOOTHING", 0.18),
    idleFloor: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_PLAYBACK_IDLE_FLOOR", 0.03),
  },
  sphere: {
    sizePx: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SPHERE_SIZE_PX", 186),
    innerInsetPx: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SPHERE_INSET_PX", 24),
    minScale: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SPHERE_MIN_SCALE", 0.94),
    maxScale: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SPHERE_MAX_SCALE", 1.26),
    idlePulseScale: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SPHERE_IDLE_PULSE_SCALE", 1.03),
    waitingPulseScale: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SPHERE_WAITING_PULSE_SCALE", 1.08),
    playingPulseScale: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SPHERE_PLAYING_PULSE_SCALE", 1.1),
    recordPulseDurationMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_RECORD_PULSE_MS", 720),
    waitingPulseDurationMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_WAITING_PULSE_MS", 950),
    idlePulseDurationMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_IDLE_PULSE_MS", 2200),
    playingPulseDurationMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_PLAYING_PULSE_MS", 620),
    morphDurationMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_MORPH_MS", 3200),
    waveDurationMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_WAVE_MS", 1700),
    waveDelayMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_WAVE_DELAY_MS", 650),
    scaleTransitionMs: getPositiveNumberEnv("NEXT_PUBLIC_VOICE_SCALE_TRANSITION_MS", 120),
  },
} as const;
