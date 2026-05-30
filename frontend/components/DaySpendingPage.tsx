"use client";

import { useMemo, useState } from "react";

import { BottomSheetModal } from "@/components/BottomSheetModal";
import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./day-spending-page.module.css";

type DaySpendingSheetMode = "expense" | "income";

type DaySpendingPageProps = {
  initialMode: DaySpendingSheetMode;
  initialOpen?: boolean;
};

const categoryOptions = ["Дети", "Жилье", "Транспорт", "Продукты"];

const sheetCopy = {
  expense: {
    title: "Расходы на день",
    typeLabel: "Тип расхода",
    typeOptions: ["Обязательные расходы", "Переменные расходы"],
  },
  income: {
    title: "Доходы в день",
    typeLabel: "Тип дохода",
    typeOptions: ["Постоянный доход", "Разовый доход"],
  },
} as const;

export function DaySpendingPage({ initialMode, initialOpen = false }: DaySpendingPageProps) {
  const [sheetMode, setSheetMode] = useState<DaySpendingSheetMode>(initialMode);
  const [isSheetOpen, setIsSheetOpen] = useState(initialOpen);
  const [isReminderEnabled, setIsReminderEnabled] = useState(true);
  const [categoryIndex, setCategoryIndex] = useState(0);
  const [typeIndex, setTypeIndex] = useState(0);
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");

  const modeCopy = sheetCopy[sheetMode];
  const activeCategory = categoryOptions[categoryIndex];
  const activeTypeOptions = modeCopy.typeOptions;

  const activeType = useMemo(() => {
    const index = typeIndex % activeTypeOptions.length;
    return activeTypeOptions[index];
  }, [activeTypeOptions, typeIndex]);

  function handleCategoryClick() {
    setCategoryIndex((current) => (current + 1) % categoryOptions.length);
  }

  function handleTypeClick() {
    setTypeIndex((current) => (current + 1) % activeTypeOptions.length);
  }

  function openSheet(mode: DaySpendingSheetMode) {
    setSheetMode(mode);
    setTypeIndex(0);
    setDescription("");
    setAmount("");
    setIsSheetOpen(true);
  }

  function closeSheet() {
    setIsSheetOpen(false);
  }

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title={"Траты\nна день"}
          leftHref={financeRoutes.home}
          leftIcon="back"
          prizeHref={financeRoutes.achievements}
          logoutHref="/login"
        />

        <section className={styles.summaryCard} aria-label="Сводка трат на день">
          <p className={styles.summaryLabel}>Остаток на сегодня</p>
          <p className={styles.summaryValue}>
            <strong>1 300</strong>
            <span>руб</span>
          </p>

          <div className={styles.summaryDivider} aria-hidden="true" />

          <p className={styles.summaryLabel}>Лимит на день</p>
          <p className={styles.summaryValue}>
            <strong>2 000</strong>
            <span>руб</span>
          </p>
        </section>

        <section className={styles.reminderCard} aria-label="Напоминание о заполнении">
          <p className={styles.reminderText}>Напоминать о заполнении</p>

          <button
            type="button"
            className={isReminderEnabled ? styles.toggleButtonEnabled : styles.toggleButton}
            aria-label="Переключить напоминание"
            aria-pressed={isReminderEnabled}
            onClick={() => setIsReminderEnabled((current) => !current)}
          >
            <span className={isReminderEnabled ? styles.toggleThumbEnabled : styles.toggleThumb} aria-hidden="true" />
          </button>
        </section>

        <section className={styles.actionsSection} aria-label="Добавление операций за день">
          <h2 className={styles.actionsTitle}>Добавить операцию</h2>
          <div className={styles.actionsRow}>
            <button type="button" className={styles.actionButton} onClick={() => openSheet("expense")} aria-label="Добавить расход">
              Добавить расход
            </button>
            <button type="button" className={styles.actionButton} onClick={() => openSheet("income")} aria-label="Добавить доход">
              Добавить доход
            </button>
          </div>
        </section>

        <section className={styles.recommendationsSection} aria-label="Рекомендации">
          <h2 className={styles.recommendationsTitle}>Рекомендации</h2>

          <div className={styles.recommendationsCard}>
            <p className={styles.recommendationsText}>
              Рекомендуем заполнять траты ежедневно, чтобы прогноз оставался точным и полезным.
            </p>
          </div>
        </section>
      </div>

      <BottomSheetModal
        isOpen={isSheetOpen}
        onClose={closeSheet}
        ariaLabel={modeCopy.title}
        title={modeCopy.title}
        backdropClassName={styles.backdrop}
        sheetClassName={styles.sheet}
        handleClassName={styles.sheetHandle}
        titleClassName={styles.sheetTitle}
      >
        <button
          type="button"
          className={styles.fieldPillButton}
          onClick={handleCategoryClick}
          aria-label={`Категория: ${activeCategory}`}
        >
          <span className={styles.fieldLabel}>Категория</span>
          <span className={styles.fieldValue}>{activeCategory}</span>
        </button>

        <button
          type="button"
          className={styles.fieldPillButton}
          onClick={handleTypeClick}
          aria-label={`${modeCopy.typeLabel}: ${activeType}`}
        >
          <span className={styles.fieldLabel}>{modeCopy.typeLabel}</span>
          <span className={styles.fieldValue}>{activeType}</span>
        </button>

        <section className={styles.textFieldsCard} aria-label="Описание и сумма">
          <input
            className={styles.textInput}
            type="text"
            placeholder="Описание"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            aria-label="Описание"
          />

          <div className={styles.fieldDivider} aria-hidden="true" />

          <input
            className={styles.textInput}
            type="text"
            inputMode="decimal"
            placeholder="Сумма"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            aria-label="Сумма"
          />
        </section>
      </BottomSheetModal>
    </main>
  );
}
