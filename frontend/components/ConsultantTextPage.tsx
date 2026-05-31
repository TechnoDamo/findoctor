"use client";

import Image from "next/image";
import Link from "next/link";
import { Plus, SendHorizontal } from "lucide-react";
import { ChangeEvent, FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { FinanceHeader } from "@/components/FinanceHeader";
import { sendConsultantTextMessage } from "@/lib/consultantApi";
import { useConsultantChatStore } from "@/lib/consultantChatStore";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./consultant-text-page.module.css";

type ConsultantTextPageProps = {
  initialInput?: string;
};

const WELCOME_MESSAGE = "Здравствуйте! Я финансовый консультант. Чем могу помочь сегодня?";
const MAX_TEXTAREA_HEIGHT = 152;

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
        return;
      }

      reject(new Error("Не удалось прочитать изображение"));
    };
    reader.onerror = () => reject(new Error("Не удалось прочитать изображение"));
    reader.readAsDataURL(file);
  });
}

export function ConsultantTextPage({ initialInput = "" }: ConsultantTextPageProps) {
  const [textValue, setTextValue] = useState(initialInput);
  const [busy, setBusy] = useState(false);
  const textInputRef = useRef<HTMLTextAreaElement | null>(null);
  const photoInputRef = useRef<HTMLInputElement | null>(null);
  const chatAreaRef = useRef<HTMLElement | null>(null);

  const { state, appendMessage, setConversationId } = useConsultantChatStore();

  const hasChatHistory = state.messages.length > 0;
  const messages = useMemo(() => state.messages, [state.messages]);

  const resizeInput = useCallback(() => {
    const input = textInputRef.current;
    if (!input) {
      return;
    }

    input.style.height = "0px";
    const targetHeight = Math.min(input.scrollHeight, MAX_TEXTAREA_HEIGHT);
    input.style.height = `${targetHeight}px`;
    input.style.overflowY = input.scrollHeight > MAX_TEXTAREA_HEIGHT ? "auto" : "hidden";
  }, []);

  useEffect(() => {
    resizeInput();
  }, [textValue, resizeInput]);

  useEffect(() => {
    window.addEventListener("resize", resizeInput);
    return () => window.removeEventListener("resize", resizeInput);
  }, [resizeInput]);

  useEffect(() => {
    const chat = chatAreaRef.current;
    if (!chat) {
      return;
    }

    chat.scrollTop = chat.scrollHeight;
  }, [messages, busy]);

  const submitText = useCallback(async () => {
    const text = textValue.trim();

    if (!text || busy) {
      return;
    }

    const userMessageId = crypto.randomUUID();

    appendMessage({
      id: userMessageId,
      role: "user",
      source: "text",
      text,
      createdAt: new Date().toISOString(),
    });

    setTextValue("");
    setBusy(true);

    try {
      const response = await sendConsultantTextMessage(text, state.conversationId);

      if (response.conversationId) {
        setConversationId(response.conversationId);
      }

      appendMessage({
        id: response.assistantMessageId,
        role: "assistant",
        source: "text",
        text: response.responseText,
        audioUrl: response.audioUrl,
        transcript: response.transcript,
        createdAt: new Date().toISOString(),
      });
    } catch (caughtError) {
      const fallbackMessage = caughtError instanceof Error ? caughtError.message : "Ошибка отправки сообщения";

      appendMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        source: "text",
        text: `Не удалось получить ответ: ${fallbackMessage}`,
        createdAt: new Date().toISOString(),
      });
    } finally {
      setBusy(false);
    }
  }, [appendMessage, busy, setConversationId, state.conversationId, textValue]);

  const sendText = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void submitText();
  };

  const onInputKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitText();
    }
  };

  const onPhotoSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file || !file.type.startsWith("image/")) {
      return;
    }

    try {
      const imageUrl = await fileToDataUrl(file);

      appendMessage({
        id: crypto.randomUUID(),
        role: "user",
        source: "image",
        text: "Фото",
        imageUrl,
        createdAt: new Date().toISOString(),
      });
    } catch {
      appendMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        source: "text",
        text: "Не удалось загрузить фото. Попробуйте другой файл.",
        createdAt: new Date().toISOString(),
      });
    }
  };

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <section className={styles.headerZone}>
          <FinanceHeader
            title={"Мой\nконсультант"}
            leftHref={financeRoutes.home}
            leftIcon="back"
            prizeHref={financeRoutes.achievements}
            logoutHref="/login"
            titleClassName={styles.headerTitle}
          />
        </section>

        <section ref={chatAreaRef} className={styles.chatArea} aria-label="Чат с консультантом">
          {!hasChatHistory && <article className={styles.aiMessage}>{WELCOME_MESSAGE}</article>}

          {messages.map((message) => {
            const isUser = message.role === "user";
            const isImageMessage = Boolean(message.imageUrl);

            return (
              <article
                key={message.id}
                className={`${isUser ? styles.userMessage : styles.aiMessage} ${isImageMessage ? styles.imageMessage : ""}`.trim()}
              >
                {isImageMessage ? (
                  <Image src={message.imageUrl ?? ""} alt={message.text || "Отправленное фото"} width={280} height={186} className={styles.messageImage} unoptimized />
                ) : (
                  message.text
                )}
              </article>
            );
          })}

          {busy && (
            <article className={styles.aiMessage}>
              Консультант формирует ответ...
            </article>
          )}
        </section>

        <form className={styles.inputBar} onSubmit={sendText} aria-label="Поле ввода сообщения">
          <input ref={photoInputRef} type="file" accept="image/*" className={styles.hiddenPhotoInput} onChange={onPhotoSelected} />

          <button type="button" className={styles.addPhotoButton} aria-label="Добавить фото" onClick={() => photoInputRef.current?.click()}>
            <Plus size={20} strokeWidth={2.4} />
          </button>

          <textarea
            ref={textInputRef}
            className={styles.textInput}
            placeholder="Введите текст"
            aria-label="Введите текст"
            value={textValue}
            onChange={(event) => setTextValue(event.target.value)}
            onKeyDown={onInputKeyDown}
            disabled={busy}
            rows={1}
          />

          <Link href={financeRoutes.consultantAudio} className={styles.voiceButton} aria-label="Перейти в голосовой ввод">
            <Image src="/icons/finance/consultant-mic.svg" alt="" width={27} height={27} />
          </Link>

          <button type="submit" className={styles.sendButton} aria-label="Отправить сообщение" disabled={busy || !textValue.trim()}>
            <SendHorizontal size={18} strokeWidth={2.5} />
          </button>
        </form>
      </div>
    </main>
  );
}
