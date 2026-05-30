"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

import { FinanceHeader } from "@/components/FinanceHeader";
import { sendConsultantTextMessage } from "@/lib/consultantApi";
import { useConsultantChatStore } from "@/lib/consultantChatStore";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./consultant-text-page.module.css";

type ConsultantTextPageProps = {
  initialInput?: string;
};

const WELCOME_MESSAGE = "Здравствуйте! Я финансовый консультант. Чем могу помочь сегодня?";

export function ConsultantTextPage({ initialInput = "" }: ConsultantTextPageProps) {
  const [textValue, setTextValue] = useState(initialInput);
  const [busy, setBusy] = useState(false);

  const { state, appendMessage, setConversationId } = useConsultantChatStore();

  const hasChatHistory = state.messages.length > 0;
  const messages = useMemo(() => state.messages, [state.messages]);

  const sendText = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

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

        <section className={styles.chatArea} aria-label="Чат с консультантом">
          {!hasChatHistory && <article className={styles.aiMessage}>{WELCOME_MESSAGE}</article>}

          {messages.map((message) => {
            const isUser = message.role === "user";

            return (
              <article key={message.id} className={isUser ? styles.userMessage : styles.aiMessage}>
                {message.text}
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
          <button type="submit" className={styles.sendButton} aria-label="Отправить сообщение" disabled={busy || !textValue.trim()}>
            ↗
          </button>

          <input
            className={styles.textInput}
            placeholder="Введите текст"
            aria-label="Введите текст"
            value={textValue}
            onChange={(event) => setTextValue(event.target.value)}
            disabled={busy}
          />

          <Link href={financeRoutes.consultantAudio} className={styles.voiceButton} aria-label="Перейти в голосовой ввод">
            <Image src="/icons/finance/consultant-mic.svg" alt="" width={27} height={27} />
          </Link>
        </form>
      </div>
    </main>
  );
}
