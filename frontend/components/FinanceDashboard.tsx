"use client";

import clsx from "clsx";
import { ChevronRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";

import { BottomSheetModal } from "@/components/BottomSheetModal";
import { FinanceHeader } from "@/components/FinanceHeader";
import { financeMetrics, formatRub, getCushionStats, numberFormatter } from "@/lib/financeData";
import { financeRoutes } from "@/lib/financeRoutes";

import modalStyles from "./finance.module.css";
import styles from "./finance-dashboard.module.css";

type FinanceRow = {
  id: string;
  href?: string;
  icon?: string;
  iconNode?: ReactNode;
  label: string;
  amountRub?: number;
  onClick?: () => void;
};

const summary = {
  deltaRub: 186000,
  points: financeMetrics.points,
  balanceRub: financeMetrics.balanceRub,
};

const incomeExpenseRows: FinanceRow[] = [
  { id: "income", href: financeRoutes.income, icon: "/icons/finance/income.svg", label: "Доходы", amountRub: financeMetrics.incomeRub },
  { id: "expenses", href: financeRoutes.expenses, icon: "/icons/finance/expenses.svg", label: "Расходы", amountRub: financeMetrics.expensesRub },
];

function FinanceRowAction({ row }: { row: FinanceRow }) {
  const content = (
    <>
      <span className={styles.rowLeft}>
        {row.icon ? (
          <Image src={row.icon} alt="" width={27} height={27} className={styles.rowIcon} />
        ) : (
          <span className={styles.rowIconWrap}>{row.iconNode}</span>
        )}
        <span className={styles.rowLabel}>{row.label}</span>
      </span>

      <span className={styles.rowRight}>
        {typeof row.amountRub === "number" ? <span className={styles.amountPill}>{formatRub(row.amountRub)}</span> : null}
        <ChevronRight size={24} strokeWidth={2.2} />
      </span>
    </>
  );

  if (row.onClick) {
    return (
      <button type="button" className={styles.rowButton} onClick={row.onClick} aria-label={row.label}>
        {content}
      </button>
    );
  }

  return (
    <Link className={styles.rowButton} href={row.href ?? "#"} aria-label={row.label}>
      {content}
    </Link>
  );
}

export function FinanceDashboard() {
  const [isCushionOpen, setIsCushionOpen] = useState(false);
  const [notifyEnabled, setNotifyEnabled] = useState(true);
  const cushionStats = useMemo(() => getCushionStats(financeMetrics), []);
  const [autoTopUpValue, setAutoTopUpValue] = useState(() => formatRub(cushionStats.autoTopUpRub));
  const controlRows: FinanceRow[] = [
    { id: "credit-traffic", href: financeRoutes.creditTraffic, icon: "/icons/finance/traffic.svg", label: "Кредитный светофор" },
    { id: "savings", href: financeRoutes.savings, icon: "/icons/finance/savings.svg", label: "Копилка", amountRub: 50000 },
    {
      id: "cushion",
      icon: "/icons/finance/cushion.svg",
      label: "Подушка",
      amountRub: financeMetrics.cushionRub,
      onClick: () => setIsCushionOpen(true),
    },
  ];

  return (
    <main className={styles.financeScreen}>
      <div className={styles.contentWrap}>
        <FinanceHeader
          title="Профиит"
          leftHref={financeRoutes.profile}
          leftIcon="avatar"
          prizeHref={financeRoutes.achievements}
          logoutHref="/login"
          headerClassName={styles.header}
          headerRightClassName={styles.headerRight}
          titleClassName={styles.headerTitle}
          actionClassName={styles.headerAction}
        />

        <section className={styles.summaryCard}>
          <p className={styles.summaryCaption}>Доходы - Расходы в мес</p>
          <div className={styles.summaryMainRow}>
            <p className={styles.summaryDelta}>
              <strong>+ {numberFormatter.format(summary.deltaRub)}</strong>
              <span>руб</span>
            </p>
            <p className={styles.pointsPill}>
              <strong>{summary.points}</strong>
              <span>балла</span>
            </p>
          </div>

          <p className={styles.balanceCaption}>Общий баланс</p>

          <div className={styles.summaryBottomRow}>
            <span className={styles.balancePill}>
              <strong>{numberFormatter.format(summary.balanceRub)}</strong>
              <span>руб</span>
            </span>
            <Link className={styles.dailySpendButton} href={financeRoutes.daySpending}>
              <span>
                Потратил
                <br />
                на день →
              </span>
            </Link>
          </div>
        </section>

        <section className={clsx(styles.listCard, styles.incomeExpenseList)} aria-label="Доходы и расходы">
          {incomeExpenseRows.map((row) => (
            <div className={styles.listItem} key={row.id}>
              <FinanceRowAction row={row} />
            </div>
          ))}
        </section>

        <section className={clsx(styles.listCard, styles.controlList)} aria-label="Контрольные блоки">
          {controlRows.map((row) => (
            <div className={styles.listItem} key={row.id}>
              <FinanceRowAction row={row} />
            </div>
          ))}
        </section>

        <Link className={styles.consultantButton} href={financeRoutes.consultant}>
          <span>
            Мой
            <br />
            Консультант
          </span>
        </Link>
      </div>

      <BottomSheetModal
        isOpen={isCushionOpen}
        onClose={() => setIsCushionOpen(false)}
        ariaLabel="Подушка безопасности"
        title="Подушка"
        titleClassName={modalStyles.cushionTitle}
        backdropClassName={modalStyles.cushionBackdrop}
        sheetClassName={modalStyles.cushionSheet}
        handleClassName={modalStyles.cushionHandle}
      >
        <section className={modalStyles.amountCard}>
          <p className={modalStyles.amount}>
            <strong>{formatRub(financeMetrics.cushionRub).replace(" руб", "")}</strong>
            <span>руб</span>
          </p>

          <p className={modalStyles.daysPill}>
            На <strong>~{cushionStats.daysCovered}</strong> дня
          </p>
        </section>

        <section className={modalStyles.autoTopupCard}>
          <p className={modalStyles.autoTopupTitle}>Авто-пополнение в мес</p>
          <div className={modalStyles.autoTopupDivider} aria-hidden="true" />
          <label className={modalStyles.autoTopupValueRow}>
            <input
              className={modalStyles.autoTopupInput}
              type="text"
              value={autoTopUpValue}
              onChange={(event) => setAutoTopUpValue(event.target.value)}
              aria-label="Сумма автопополнения"
            />
            <span className={modalStyles.autoTopupSuffix}>мес</span>
          </label>
        </section>

        <section className={modalStyles.notifyCard} aria-label="Уведомления о пополнении">
          <p className={modalStyles.notifyLabel}>Уведомлять о пополнении</p>
          <button
            type="button"
            className={modalStyles.notifySwitch}
            data-checked={notifyEnabled}
            aria-label="Переключить уведомления о пополнении"
            aria-pressed={notifyEnabled}
            onClick={() => setNotifyEnabled((current) => !current)}
          />
        </section>

        <h3 className={modalStyles.recommendationsTitle}>Рекомендации</h3>

        <section className={modalStyles.recommendationCard}>
          <p className={modalStyles.recommendationText}>
            У вас хорошая подушка безопасности
            <br />
            <br />
            Можете продолжать в том же духе.
            <br />
            Если хотите увеличить, то можно
            <br />
            перестать пить кофе
          </p>

          <Link className={modalStyles.detailsButton} href={financeRoutes.consultant}>
            Подробнее
          </Link>
        </section>
      </BottomSheetModal>
    </main>
  );
}
