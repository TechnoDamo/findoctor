"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { FinanceHeader } from "@/components/FinanceHeader";

import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./savings-page.module.css";

const SAVINGS_AMOUNT_STORAGE_KEY = "savings_page_amount_rub";
const DEFAULT_SAVINGS_AMOUNT = "50000";

function normalizeAmountInput(value: string) {
  return value.replace(/[^\d]/g, "");
}

export function SavingsPage() {
  const [savingsAmount, setSavingsAmount] = useState(() => {
    if (typeof window === "undefined") {
      return DEFAULT_SAVINGS_AMOUNT;
    }

    try {
      const savedValue = window.localStorage.getItem(SAVINGS_AMOUNT_STORAGE_KEY);
      const normalized = normalizeAmountInput(savedValue ?? "");
      return normalized || DEFAULT_SAVINGS_AMOUNT;
    } catch {
      return DEFAULT_SAVINGS_AMOUNT;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(SAVINGS_AMOUNT_STORAGE_KEY, savingsAmount || "0");
    } catch {
      // Ignore storage failures.
    }
  }, [savingsAmount]);

  const formattedSavingsAmount = useMemo(() => {
    const parsedValue = Number.parseInt(savingsAmount || "0", 10);

    if (!Number.isFinite(parsedValue)) {
      return "0";
    }

    return new Intl.NumberFormat("ru-RU").format(parsedValue);
  }, [savingsAmount]);

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title="Копилка"
          leftHref={financeRoutes.home}
          leftIcon="back"
          prizeHref={financeRoutes.profile}
          logoutHref="/login"
        />

        <section className={styles.goalCard} aria-label="Параметры цели накопления">
          <button type="button" className={`${styles.goalField} ${styles.pressableNeutral}`}>
            Цель накопления
          </button>

          <div className={styles.goalRow}>
            <button type="button" className={`${styles.goalField} ${styles.goalFieldDate} ${styles.pressableNeutral}`}>
              Дата окончания
            </button>

            <label className={`${styles.goalField} ${styles.goalFieldAmount} ${styles.goalAmountField}`} aria-label="Сумма накопления">
              <input
                className={styles.goalAmountInput}
                type="text"
                inputMode="numeric"
                value={savingsAmount}
                onChange={(event) => setSavingsAmount(normalizeAmountInput(event.target.value))}
                placeholder="Сумма"
              />
            </label>
          </div>
        </section>

        <button type="button" className={`${styles.autoTopupCard} ${styles.pressableNeutral}`} aria-label="Авто-пополнение в месяц">
          <span className={styles.autoTopupTitle}>Авто-пополнение в мес</span>
          <span className={styles.autoTopupSeparator} aria-hidden="true" />
          <span className={styles.autoTopupValue}>0 руб мес</span>
        </button>

        <button type="button" className={`${styles.progressCard} ${styles.pressableNeutral}`} aria-label="Сколько накопили">
          <span className={styles.progressTitle}>Сколько накопили</span>
          <span className={styles.progressTrack} aria-hidden="true">
            <span className={styles.progressFill} />
            <span className={styles.progressValue}>{formattedSavingsAmount} руб</span>
          </span>
        </button>

        <h2 className={styles.recommendationsTitle}>Рекомендации</h2>

        <section className={styles.recommendationCard} aria-label="Рекомендация по накоплению">
          <p className={styles.recommendationText}>
            В настоящих реалях, вы не сможете
            <br />
            накопить на цель.
            <br />
            Предлагаю сдвинуть дату окончания, при
            <br />
            вашей долговой нагрузки вы можете в
            <br />
            месяц откладывать 30 000 руб в мес, вы
            <br />
            достигните цели через 50 мес
          </p>

          <button type="button" className={styles.chatButton}>
            Продолжить в чате
          </button>
        </section>

        <Link href={financeRoutes.consultant} className={`${styles.partnerCard} ${styles.pressableNeutral}`} aria-label="ООО Машины">
          <span className={styles.partnerImageWrap} aria-hidden="true">
            <Image src="/icons/finance/partner-cars.png" alt="" fill sizes="134px" className={styles.partnerImage} />
          </span>

          <span className={styles.partnerTextArea}>
            <span className={styles.partnerTitle}>ООО Машины</span>
            <span className={styles.partnerDescription}>
              Чтобы закрыть цель выгодно,
              <br />
              предлагаем оформить
              <br />
              машину у наших партнеров
            </span>
          </span>
        </Link>

        <h2 className={styles.planTitle}>
          План накопления
          <br />
          Чтобы успеть вовремя
        </h2>

        <section className={styles.planCard} aria-label="План накопления">
          <div className={`${styles.planRow} ${styles.planRowDay}`}>
            <span className={styles.planLabel}>В день</span>
            <span className={`${styles.planBadge} ${styles.planBadgeShort}`}>50 руб</span>
          </div>

          <div className={styles.planSeparator} aria-hidden="true" />

          <div className={`${styles.planRow} ${styles.planRowWeek}`}>
            <span className={styles.planLabel}>В неделю</span>
            <span className={`${styles.planBadge} ${styles.planBadgeShort}`}>350 руб</span>
          </div>

          <div className={styles.planSeparator} aria-hidden="true" />

          <div className={`${styles.planRow} ${styles.planRowMonth}`}>
            <span className={styles.planLabel}>В месяц</span>
            <span className={`${styles.planBadge} ${styles.planBadgeLong}`}>1 500 руб</span>
          </div>
        </section>
      </div>
    </main>
  );
}
