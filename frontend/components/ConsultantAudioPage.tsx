"use client";

import { useState } from "react";
import Link from "next/link";

import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./consultant-audio-page.module.css";

export function ConsultantAudioPage() {
  const [recording, setRecording] = useState(true);

  return (
    <main className={styles.page}>
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
          <h2 className={styles.voiceTitle}>Говорите</h2>

          <button
            type="button"
            className={`${styles.voiceCircle} ${recording ? styles.recording : ""}`}
            onClick={() => setRecording((value) => !value)}
            aria-label={recording ? "Остановить голосовой ввод" : "Запустить голосовой ввод"}
            aria-pressed={recording}
          >
            <span className={styles.voiceCircleInner} aria-hidden="true" />
          </button>
        </section>

        <Link className={styles.backToChatButton} href={financeRoutes.consultant}>
          Вернуться в чат
        </Link>
      </div>
    </main>
  );
}
