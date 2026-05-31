"use client";

import { useCallback, useMemo, useState } from "react";

import { consultantConfig } from "@/lib/consultantConfig";
import type { ConsultantChatState, ConsultantMessage } from "@/lib/consultantTypes";

const CONSULTANT_CHAT_STORAGE_KEY = "findoctor_consultant_chat_state_v1";

const emptyState: ConsultantChatState = {
  conversationId: null,
  messages: [],
};

function limitMessages(messages: ConsultantMessage[]): ConsultantMessage[] {
  const { maxMessages } = consultantConfig.storage;

  if (messages.length <= maxMessages) {
    return messages;
  }

  return messages.slice(messages.length - maxMessages);
}

function readState(): ConsultantChatState {
  if (typeof window === "undefined") {
    return emptyState;
  }

  try {
    const raw = window.localStorage.getItem(CONSULTANT_CHAT_STORAGE_KEY);

    if (!raw) {
      return emptyState;
    }

    const parsed = JSON.parse(raw) as ConsultantChatState;

    if (!parsed || typeof parsed !== "object") {
      return emptyState;
    }

    const conversationId = typeof parsed.conversationId === "string" ? parsed.conversationId : null;
    const messages = Array.isArray(parsed.messages)
      ? parsed.messages.filter(
          (message) =>
            message &&
            (typeof message.text === "string" || (typeof message.imageUrl === "string" && message.imageUrl.length > 0)),
        )
      : [];

    return {
      conversationId,
      messages: limitMessages(messages),
    };
  } catch {
    return emptyState;
  }
}

function writeState(state: ConsultantChatState): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(CONSULTANT_CHAT_STORAGE_KEY, JSON.stringify(state));
}

export function useConsultantChatStore() {
  const [state, setState] = useState<ConsultantChatState>(() => readState());

  const applyState = useCallback((updater: (previous: ConsultantChatState) => ConsultantChatState) => {
    setState((previous) => {
      const nextState = updater(previous);
      writeState(nextState);
      return nextState;
    });
  }, []);

  const appendMessage = useCallback(
    (message: ConsultantMessage) => {
      applyState((previous) => ({
        ...previous,
        messages: limitMessages([...previous.messages, message]),
      }));
    },
    [applyState],
  );

  const updateMessage = useCallback(
    (id: string, patch: Partial<ConsultantMessage>) => {
      applyState((previous) => ({
        ...previous,
        messages: previous.messages.map((message) =>
          message.id === id
            ? {
                ...message,
                ...patch,
              }
            : message,
        ),
      }));
    },
    [applyState],
  );

  const setConversationId = useCallback(
    (conversationId: string | null) => {
      applyState((previous) => ({
        ...previous,
        conversationId,
      }));
    },
    [applyState],
  );

  const clearHistory = useCallback(() => {
    writeState(emptyState);
    setState(emptyState);
  }, []);

  return useMemo(
    () => ({
      state,
      appendMessage,
      updateMessage,
      setConversationId,
      clearHistory,
    }),
    [appendMessage, clearHistory, setConversationId, state, updateMessage],
  );
}
