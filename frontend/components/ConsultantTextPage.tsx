"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./consultant-text-page.module.css";

type ConsultantTextPageProps = {
  initialInput?: string;
};

export function ConsultantTextPage({ initialInput = "" }: ConsultantTextPageProps) {
  const [textValue, setTextValue] = useState(initialInput);

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
          <article className={styles.aiMessage}>
            Рекомендую вам не брать кредит еще
            <br />У вас большая долговая нагрузка
          </article>

          <article className={styles.userMessage}>
            А если купить каблуки,
            <br />на них скидка 70%
          </article>

          <div className={styles.userImageMessage} aria-label="Изображение пользователя">
            <div className={styles.userImageFrame}>
              <Image src="/icons/finance/partner-cars.png" alt="" fill sizes="191px" />
            </div>
          </div>
        </section>

        <form className={styles.inputBar} action="#" aria-label="Поле ввода сообщения">
          <button type="button" className={styles.addButton} aria-label="Добавить вложение">
            +
          </button>

          <input
            className={styles.textInput}
            placeholder="Введите текст"
            aria-label="Введите текст"
            value={textValue}
            onChange={(event) => setTextValue(event.target.value)}
          />

          <Link href={financeRoutes.consultantAudio} className={styles.voiceButton} aria-label="Перейти в голосовой ввод">
            <Image src="/icons/finance/consultant-mic.svg" alt="" width={27} height={27} />
          </Link>
        </form>
      </div>
    </main>
  );
}
