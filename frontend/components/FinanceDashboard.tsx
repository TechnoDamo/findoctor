"use client";

import clsx from "clsx";
import { ChevronRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

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
const BALANCE_PILL_MIN_WIDTH = 118;
const BALANCE_PILL_MAX_WIDTH = 188;

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
  const [balanceValue, setBalanceValue] = useState(() => numberFormatter.format(summary.balanceRub));
  const balanceInputRef = useRef<HTMLTextAreaElement | null>(null);
  const balancePillRef = useRef<HTMLLabelElement | null>(null);
  const balanceSuffixRef = useRef<HTMLSpanElement | null>(null);
  const balanceMeasureCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const cushionStats = useMemo(() => getCushionStats(financeMetrics), []);
  const [autoTopUpValue, setAutoTopUpValue] = useState(() => formatRub(cushionStats.autoTopUpRub));

  const syncBalanceInputSize = useCallback(() => {
    const input = balanceInputRef.current;
    const pill = balancePillRef.current;
    const suffix = balanceSuffixRef.current;
    if (!input || !pill || !suffix) {
      return;
    }

    const computedPillStyles = window.getComputedStyle(pill);
    const computedInputStyles = window.getComputedStyle(input);
    const paddingLeft = Number.parseFloat(computedPillStyles.paddingLeft) || 0;
    const paddingRight = Number.parseFloat(computedPillStyles.paddingRight) || 0;
    const horizontalPadding = paddingLeft + paddingRight;
    const gap = Number.parseFloat(computedPillStyles.columnGap || computedPillStyles.gap) || 0;
    const suffixWidth = suffix.offsetWidth;
    const letterSpacing = computedInputStyles.letterSpacing === "normal" ? 0 : Number.parseFloat(computedInputStyles.letterSpacing) || 0;
    const text = balanceValue;
    const canvas = balanceMeasureCanvasRef.current ?? document.createElement("canvas");
    balanceMeasureCanvasRef.current = canvas;
    const context = canvas.getContext("2d");
    let contentWidth = 1;
    if (context) {
      context.font = `${computedInputStyles.fontWeight} ${computedInputStyles.fontSize} ${computedInputStyles.fontFamily}`;
      const measuredTextWidth = Math.ceil(context.measureText(text).width);
      const spacingWidth = text.length > 1 ? Math.ceil((text.length - 1) * letterSpacing) : 0;
      contentWidth = Math.max(1, measuredTextWidth + spacingWidth);
    }

    const maxInputWidth = BALANCE_PILL_MAX_WIDTH - horizontalPadding - gap - suffixWidth;
    const targetInputWidth = Math.max(1, Math.min(contentWidth, maxInputWidth));
    const targetPillWidth = Math.max(
      BALANCE_PILL_MIN_WIDTH,
      Math.min(BALANCE_PILL_MAX_WIDTH, targetInputWidth + suffixWidth + gap + horizontalPadding),
    );
    const finalInputWidth = Math.max(1, targetPillWidth - horizontalPadding - gap - suffixWidth);

    pill.style.width = `${targetPillWidth}px`;
    input.style.width = `${finalInputWidth}px`;
    input.style.height = "0px";
    input.style.height = `${input.scrollHeight}px`;
  }, [balanceValue]);

  useEffect(() => {
    syncBalanceInputSize();
  }, [balanceValue, syncBalanceInputSize]);

  useEffect(() => {
    window.addEventListener("resize", syncBalanceInputSize);
    return () => window.removeEventListener("resize", syncBalanceInputSize);
  }, [syncBalanceInputSize]);
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
            <label ref={balancePillRef} className={styles.balancePill}>
              <textarea
                ref={balanceInputRef}
                className={styles.balanceInput}
                value={balanceValue}
                onChange={(event) => setBalanceValue(event.target.value.replace(/\n/g, ""))}
                aria-label="Общий баланс"
                rows={1}
              />
              <span ref={balanceSuffixRef}>руб</span>
            </label>
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
