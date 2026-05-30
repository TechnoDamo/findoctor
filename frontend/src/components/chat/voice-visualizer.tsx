'use client';

type VoiceState = 'idle' | 'listening' | 'processing';

interface VoiceVisualizerProps {
  state: VoiceState;
  size?: number;
  amplitude?: number;
}

export function VoiceVisualizer({ state, size = 120, amplitude = 0 }: VoiceVisualizerProps) {
  if (state === 'processing') {
    const ringCount = 3;
    return (
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        {Array.from({ length: ringCount }).map((_, i) => (
          <div
            key={i}
            className="absolute inset-0 rounded-full border-2 border-blue-400/40"
            style={{
              animation: `voice-process-ripple 1.8s ease-out ${i * 0.45}s infinite`,
            }}
          />
        ))}
        <div
          className="absolute inset-[12%] rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(59,130,246,0.9) 0%, rgba(99,102,241,0.5) 60%, transparent 100%)',
            animation: 'voice-process-glow 2s ease-in-out infinite, voice-process-center 1.5s ease-in-out infinite',
          }}
        />
      </div>
    );
  }

  if (state === 'listening') {
    const a = amplitude;
    const ringScale = (base: number) => base + a * 0.45;
    const innerScale = 0.85 + a * 0.55;
    const ringOpacity = (level: number) => Math.max(0.05, (0.7 - level * 0.2) * (0.4 + a * 0.6)).toFixed(2);

    return (
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <div
          className="absolute inset-0 rounded-full border-2 border-red-400"
          style={{
            transform: `scale(${ringScale(0.8)})`,
            opacity: ringOpacity(0),
            animation: 'voice-listening-ring1 0.8s ease-in-out infinite',
            transition: 'transform 0.08s ease-out',
          }}
        />
        <div
          className="absolute inset-0 rounded-full border-2 border-red-400/70"
          style={{
            transform: `scale(${ringScale(0.95)})`,
            opacity: ringOpacity(1),
            animation: 'voice-listening-ring2 0.8s ease-in-out 0.15s infinite',
            transition: 'transform 0.08s ease-out',
          }}
        />
        <div
          className="absolute inset-0 rounded-full border-2 border-red-400/40"
          style={{
            transform: `scale(${ringScale(1.1)})`,
            opacity: ringOpacity(2),
            animation: 'voice-listening-ring3 0.8s ease-in-out 0.3s infinite',
            transition: 'transform 0.08s ease-out',
          }}
        />
        <div
          className="absolute rounded-full bg-red-500"
          style={{
            inset: `${(1 - innerScale) * 50}%`,
            transitionProperty: 'inset',
            transitionDuration: '80ms',
            transitionTimingFunction: 'ease-out',
          }}
        />
      </div>
    );
  }

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <div
        className="absolute inset-[-10%] rounded-full bg-blue-500/15"
        style={{ animation: 'voice-idle 3s ease-in-out infinite' }}
      />
      <div className="absolute inset-0 rounded-full border-2 border-blue-400/50" />
      <div className="absolute inset-[15%] rounded-full bg-blue-500" />
    </div>
  );
}
