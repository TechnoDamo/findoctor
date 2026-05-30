"use client";

import Link from "next/link";
import { useState } from "react";

import { BottomSheetModal } from "@/components/BottomSheetModal";
import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";
import { financeMetrics, formatRub, getCushionStats } from "@/lib/financeData";

import styles from "./finance.module.css";

const cushionStats = getCushionStats(financeMetrics);

export function CushionModalPage() {
  const [notifyEnabled, setNotifyEnabled] = useState(true);
  const [autoTopUpValue, setAutoTopUpValue] = useState(() => formatRub(cushionStats.autoTopUpRub));

  return (
    <main className={styles.financeScreen}>
      <div className={styles.contentWrap}>
        <div className={styles.cushionBackground}>
          <FinanceHeader
            title="Профиит"
            leftHref={financeRoutes.profile}
            leftIcon="avatar"
            prizeHref={financeRoutes.achievements}
            logoutHref="/"
          />

          <section className={styles.summaryCard}>
            <p className={styles.summaryCaption}>Доходы - Расходы в мес</p>
          </section>
        </div>
      </div>

      <BottomSheetModal
        isOpen
        ariaLabel="Подушка безопасности"
        title="Подушка"
        titleClassName={styles.cushionTitle}
        backdropClassName={styles.cushionBackdrop}
        sheetClassName={styles.cushionSheet}
        handleClassName={styles.cushionHandle}
      >
        <section className={styles.amountCard}>
          <p className={styles.amount}>
            <strong>{formatRub(financeMetrics.cushionRub).replace(" руб", "")}</strong>
            <span>руб</span>
          </p>

          <p className={styles.daysPill}>
            На <strong>~{cushionStats.daysCovered}</strong> дня
          </p>
        </section>

        <section className={styles.autoTopupCard}>
          <p className={styles.autoTopupTitle}>Авто-пополнение в мес</p>
          <div className={styles.autoTopupDivider} aria-hidden="true" />
          <label className={styles.autoTopupValueRow}>
            <input
              className={styles.autoTopupInput}
              type="text"
              value={autoTopUpValue}
              onChange={(event) => setAutoTopUpValue(event.target.value)}
              aria-label="Сумма автопополнения"
            />
            <span className={styles.autoTopupSuffix}>мес</span>
          </label>
        </section>

        <section className={styles.notifyCard} aria-label="Уведомления о пополнении">
          <p className={styles.notifyLabel}>Уведомлять о пополнении</p>
          <button
            type="button"
            className={styles.notifySwitch}
            data-checked={notifyEnabled}
            aria-label="Переключить уведомления о пополнении"
            aria-pressed={notifyEnabled}
            onClick={() => setNotifyEnabled((current) => !current)}
          />
        </section>

        <h3 className={styles.recommendationsTitle}>Рекомендации</h3>

        <section className={styles.recommendationCard}>
          <p className={styles.recommendationText}>
            У вас хорошая подушка безопасности
            <br />
            <br />
            Можете продолжать в том же духе.
            <br />
            Если хотите увеличить, то можно
            <br />
            перестать пить кофе
          </p>

          <Link className={styles.detailsButton} href={financeRoutes.consultant}>
            Подробнее
          </Link>
        </section>
      </BottomSheetModal>
    </main>
  );
}
