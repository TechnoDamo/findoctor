"use client";

import { ChevronDown, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { BottomSheetModal } from "@/components/BottomSheetModal";
import { FinanceHeader } from "@/components/FinanceHeader";
import { financeMetrics, numberFormatter } from "@/lib/financeData";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./income-page.module.css";

type IncomeType = "Постоянный доход" | "Непостоянный доход";

type IncomeSource = {
  id: string;
  category: string;
  incomeType: IncomeType;
  name: string;
  amountRub: number;
};

type IncomeForm = {
  category: string;
  incomeType: IncomeType;
  name: string;
  monthlyAmount: string;
};

type SheetState =
  | { mode: "create" }
  | { mode: "edit"; id: string }
  | null;

type FormErrors = Record<string, string>;

const categoryOptions = ["Работа", "Фриланс", "Бизнес", "Инвестиции", "Подработки", "Другое"];
const incomeTypeOptions: IncomeType[] = ["Постоянный доход", "Непостоянный доход"];

const initialIncomeSources: IncomeSource[] = [
  { id: "dev-work", category: "Работа", incomeType: "Постоянный доход", name: "Работа разработчика", amountRub: 150000 },
  { id: "freelance", category: "Фриланс", incomeType: "Непостоянный доход", name: "Фриланс", amountRub: 90000 },
];

function parseNumber(raw: string) {
  const normalized = raw.replace(/\s+/g, "").replace(/,/g, ".");

  if (!normalized) {
    return Number.NaN;
  }

  return Number(normalized);
}

function buildIncomeForm(item?: IncomeSource): IncomeForm {
  if (!item) {
    return {
      category: categoryOptions[0],
      incomeType: incomeTypeOptions[0],
      name: "",
      monthlyAmount: "",
    };
  }

  return {
    category: item.category,
    incomeType: item.incomeType,
    name: item.name,
    monthlyAmount: String(item.amountRub),
  };
}

export function IncomePage() {
  const [incomeSources, setIncomeSources] = useState<IncomeSource[]>(initialIncomeSources);
  const [sheet, setSheet] = useState<SheetState>(null);
  const [incomeForm, setIncomeForm] = useState<IncomeForm>(buildIncomeForm());
  const [errors, setErrors] = useState<FormErrors>({});

  const isSheetOpen = sheet !== null;

  const totalIncomeRub = useMemo(
    () => incomeSources.reduce((sum, source) => sum + source.amountRub, 0),
    [incomeSources],
  );

  function closeSheet() {
    setSheet(null);
    setErrors({});
  }

  function openCreateIncomeSheet() {
    setIncomeForm(buildIncomeForm());
    setErrors({});
    setSheet({ mode: "create" });
  }

  function openEditIncomeSheet(incomeId: string) {
    const item = incomeSources.find((entry) => entry.id === incomeId);

    if (!item) {
      return;
    }

    setIncomeForm(buildIncomeForm(item));
    setErrors({});
    setSheet({ mode: "edit", id: incomeId });
  }

  function validateIncomeForm() {
    const nextErrors: FormErrors = {};

    if (!incomeForm.category.trim()) {
      nextErrors.category = "Выберите категорию";
    }

    if (!incomeForm.incomeType.trim()) {
      nextErrors.incomeType = "Выберите тип дохода";
    }

    if (!incomeForm.name.trim()) {
      nextErrors.name = "Введите источник дохода";
    }

    const monthlyAmount = parseNumber(incomeForm.monthlyAmount);

    if (!Number.isFinite(monthlyAmount) || monthlyAmount <= 0) {
      nextErrors.monthlyAmount = "Введите сумму больше нуля";
    }

    return {
      isValid: Object.keys(nextErrors).length === 0,
      errors: nextErrors,
      monthlyAmount,
    };
  }

  function submitIncome() {
    const validation = validateIncomeForm();

    setErrors(validation.errors);

    if (!validation.isValid) {
      return;
    }

    const monthlyAmountRub = Math.round(validation.monthlyAmount);

    if (sheet?.mode === "edit") {
      setIncomeSources((current) =>
        current.map((item) =>
          item.id === sheet.id
            ? {
                ...item,
                category: incomeForm.category,
                incomeType: incomeForm.incomeType,
                name: incomeForm.name.trim(),
                amountRub: monthlyAmountRub,
              }
            : item,
        ),
      );
      closeSheet();
      return;
    }

    const newIncome: IncomeSource = {
      id: `income-${crypto.randomUUID()}`,
      category: incomeForm.category,
      incomeType: incomeForm.incomeType,
      name: incomeForm.name.trim(),
      amountRub: monthlyAmountRub,
    };

    setIncomeSources((current) => [newIncome, ...current]);
    closeSheet();
  }

  function deleteIncome() {
    if (sheet?.mode !== "edit") {
      return;
    }

    setIncomeSources((current) => current.filter((item) => item.id !== sheet.id));
    closeSheet();
  }

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title="Доходы"
          leftHref={financeRoutes.home}
          leftIcon="back"
          prizeHref={financeRoutes.profile}
          logoutHref="/login"
        />

        <section className={styles.summaryCard} aria-label="Сводка доходов">
          <div className={styles.summaryLeft}>
            <p className={styles.summaryLabel}>Ваш доход мес</p>
            <p className={styles.summaryValue}>
              <strong>{numberFormatter.format(totalIncomeRub)}</strong>
              <span>руб</span>
            </p>
          </div>

          <div className={styles.expenseBadge}>
            <p className={styles.expenseLabel}>Расход</p>
            <p className={styles.expenseValue}>
              <strong>{numberFormatter.format(financeMetrics.expensesRub)}</strong>
              <span>руб</span>
            </p>
          </div>
        </section>

        <section className={styles.sourcesSection} aria-label="Источники дохода">
          <div className={styles.sourcesHeader}>
            <h2 className={styles.sectionTitle}>Источники дохода</h2>
            <button className={styles.addButton} type="button" onClick={openCreateIncomeSheet} aria-label="Добавить источник дохода">
              +
            </button>
          </div>

          <div className={styles.sourcesList}>
            {incomeSources.map((source) => (
              <button
                className={styles.sourceCard}
                key={source.id}
                type="button"
                onClick={() => openEditIncomeSheet(source.id)}
                aria-label={`${source.name} ${numberFormatter.format(source.amountRub)} руб`}
              >
                <span className={styles.sourceName}>{source.name}</span>
                <span className={styles.sourceAmount}>{numberFormatter.format(source.amountRub)} руб</span>
              </button>
            ))}
          </div>
        </section>

        <section className={styles.recommendationSection} aria-label="Рекомендации">
          <h2 className={styles.sectionTitle}>Рекомендации</h2>

          <div className={styles.recommendationCard}>
            <p className={styles.recommendationText}>
              Учитывая доходы и расходы, вы получаете больше 2% населения, у вас очень мало расходов
            </p>

            <button className={styles.chatButton} type="button" aria-label="Продолжить в чате">
              Продолжить в чате
            </button>
          </div>
        </section>
      </div>

      <BottomSheetModal
        isOpen={isSheetOpen}
        onClose={closeSheet}
        ariaLabel={sheet?.mode === "edit" ? "Редактировать доход" : "Добавить доход"}
        title={sheet?.mode === "edit" ? "Редактировать доход" : "Добавить доход"}
        backdropClassName={styles.sheetBackdrop}
        sheetClassName={styles.sheet}
        handleClassName={styles.sheetHandle}
        titleClassName={styles.sheetTitle}
      >
        <form
          className={styles.sheetForm}
          onSubmit={(event) => {
            event.preventDefault();
            submitIncome();
          }}
        >
          <label className={styles.selectPillField}>
            <select
              className={`${styles.selectPill} ${incomeForm.category ? styles.selectPillSelected : ""}`}
              value={incomeForm.category}
              onChange={(event) => setIncomeForm((current) => ({ ...current, category: event.target.value }))}
              aria-label="Выбрать категорию дохода"
            >
              <option value="">Категория</option>
              {categoryOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <ChevronDown className={styles.selectChevron} size={20} strokeWidth={2} />
          </label>
          {errors.category ? <p className={styles.formError}>{errors.category}</p> : null}

          <label className={styles.selectPillField}>
            <select
              className={`${styles.selectPill} ${incomeForm.incomeType ? styles.selectPillSelected : ""}`}
              value={incomeForm.incomeType}
              onChange={(event) => setIncomeForm((current) => ({ ...current, incomeType: event.target.value as IncomeType }))}
              aria-label="Выбрать тип дохода"
            >
              <option value="">Тип дохода</option>
              {incomeTypeOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <ChevronDown className={styles.selectChevron} size={20} strokeWidth={2} />
          </label>
          {errors.incomeType ? <p className={styles.formError}>{errors.incomeType}</p> : null}

          <div className={styles.inputCard}>
            <label className={styles.inputLabel} htmlFor="income-name">
              Источник дохода
            </label>
            <input
              id="income-name"
              className={styles.textInput}
              value={incomeForm.name}
              onChange={(event) => setIncomeForm((current) => ({ ...current, name: event.target.value }))}
            />

            <div className={styles.fieldDivider} />

            <label className={styles.inputLabel} htmlFor="income-monthly-amount">
              Сумма в мес
            </label>
            <input
              id="income-monthly-amount"
              className={styles.textInput}
              inputMode="numeric"
              pattern="[0-9]*"
              value={incomeForm.monthlyAmount}
              onChange={(event) => setIncomeForm((current) => ({ ...current, monthlyAmount: event.target.value }))}
            />
          </div>
          {errors.name ? <p className={styles.formError}>{errors.name}</p> : null}
          {errors.monthlyAmount ? <p className={styles.formError}>{errors.monthlyAmount}</p> : null}

          <div className={styles.sheetActions}>
            {sheet?.mode === "edit" ? (
              <button className={styles.sheetDeleteButton} type="button" onClick={deleteIncome}>
                <Trash2 size={16} /> Удалить
              </button>
            ) : null}
            <button className={styles.sheetSaveButton} type="submit">
              {sheet?.mode === "edit" ? "Сохранить" : "Добавить"}
            </button>
          </div>
        </form>
      </BottomSheetModal>
    </main>
  );
}
