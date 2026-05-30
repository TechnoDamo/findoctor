import { buildBackendUrl } from "@/lib/api";
import { consultantConfig } from "@/lib/consultantConfig";

type AiAudioPayload = {
  url?: string;
  base64?: string;
  contentType?: string;
  content_type?: string;
};

type AiOutputPayload = {
  text?: string;
  transcript?: string;
  audio?: AiAudioPayload | null;
};

type AiResponsePayload = {
  conversationId?: string;
  assistantMessageId?: string;
  requestText?: string;
  output?: AiOutputPayload;
};

export type ConsultantAssistantResponse = {
  conversationId: string | null;
  assistantMessageId: string;
  responseText: string;
  requestText: string | null;
  transcript: string | null;
  audioUrl: string | null;
};

function asNonEmptyString(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function audioUrlFromPayload(audio: AiAudioPayload | null | undefined): string | null {
  if (!audio) {
    return null;
  }

  const directUrl = asNonEmptyString(audio.url);

  if (directUrl) {
    return directUrl;
  }

  const base64 = asNonEmptyString(audio.base64);

  if (!base64) {
    return null;
  }

  const contentType = asNonEmptyString(audio.contentType) ?? asNonEmptyString(audio.content_type) ?? "audio/wav";

  return `data:${contentType};base64,${base64}`;
}

async function requestJson(path: string, init: RequestInit, timeoutMs: number): Promise<AiResponsePayload> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(buildBackendUrl(path), {
      ...init,
      credentials: "include",
      signal: controller.signal,
    });

    const json = (await response.json().catch(() => ({}))) as Record<string, unknown>;

    if (!response.ok) {
      const detail = asNonEmptyString(json.detail) ?? asNonEmptyString(json.message) ?? `HTTP ${response.status}`;
      throw new Error(detail);
    }

    return json as AiResponsePayload;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function toAssistantResponse(payload: AiResponsePayload): ConsultantAssistantResponse {
  const conversationId = asNonEmptyString(payload.conversationId);
  const assistantMessageId = asNonEmptyString(payload.assistantMessageId) ?? crypto.randomUUID();
  const responseText = asNonEmptyString(payload.output?.text) ?? "Ассистент не вернул текстовый ответ";
  const requestText = asNonEmptyString(payload.requestText);
  const transcript = asNonEmptyString(payload.output?.transcript);
  const audioUrl = audioUrlFromPayload(payload.output?.audio);

  return {
    conversationId,
    assistantMessageId,
    responseText,
    requestText,
    transcript,
    audioUrl,
  };
}

export async function sendConsultantTextMessage(text: string, conversationId: string | null) {
  const payload = {
    input: [{ type: "text", text }],
    responseModalities: ["text"],
    ...(conversationId ? { conversationId } : {}),
  };

  const response = await requestJson(
    "/ai/chat/messages",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    consultantConfig.network.textTimeoutMs,
  );

  return toAssistantResponse(response);
}

export async function sendConsultantAudioMessage(blob: Blob, conversationId: string | null) {
  const formData = new FormData();
  formData.append("audio", blob, "voice.wav");
  formData.append("audioFormat", "wav");
  formData.append("responseModalities", "text,audio");

  if (conversationId) {
    formData.append("conversationId", conversationId);
  }

  const response = await requestJson(
    "/ai/chat/audio",
    {
      method: "POST",
      body: formData,
    },
    consultantConfig.network.audioTimeoutMs,
  );

  return toAssistantResponse(response);
}
