"use client";

import clsx from "clsx";
import { Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { BottomSheetModal } from "@/components/BottomSheetModal";
import { FinanceHeader } from "@/components/FinanceHeader";
import { financeMetrics, numberFormatter } from "@/lib/financeData";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./finance.module.css";

type ExpenseType = "Обязательные расходы" | "Переменные расходы";

type ExpenseItem = {
  id: string;
  category: string;
  expenseType: ExpenseType;
  description: string;
  monthlyAmountRub: number;
};

type CreditItem = {
  id: string;
  bank: string;
  loanAmountRub: number;
  termMonths: number;
  monthlyPaymentRub: number;
  interestRate?: number;
};

type ExpenseForm = {
  category: string;
  expenseType: ExpenseType;
  description: string;
  monthlyAmount: string;
};

type CreditForm = {
  bank: string;
  loanAmount: string;
  termMonths: string;
  monthlyPayment: string;
  interestRate: string;
};

type SheetState =
  | { kind: "expense"; mode: "create" }
  | { kind: "expense"; mode: "edit"; id: string }
  | { kind: "credit"; mode: "create" }
  | { kind: "credit"; mode: "edit"; id: string }
  | null;

type FormErrors = Record<string, string>;

const categoryOptions = ["Дети", "Подписки", "Жилье", "Транспорт", "Здоровье"];
const expenseTypeOptions: ExpenseType[] = ["Обязательные расходы", "Переменные расходы"];

const initialExpenses: ExpenseItem[] = [
  {
    id: "exp-1",
    category: "Дети",
    expenseType: "Обязательные расходы",
    description: "Детям на еду",
    monthlyAmountRub: 40000,
  },
  {
    id: "exp-2",
    category: "Подписки",
    expenseType: "Переменные расходы",
    description: "Подписки на GPT",
    monthlyAmountRub: 7000,
  },
];

const initialCredits: CreditItem[] = [
  {
    id: "cred-1",
    bank: "СберБанк",
    loanAmountRub: 450000,
    termMonths: 46,
    monthlyPaymentRub: 7000,
    interestRate: 13.5,
  },
];

function formatRub(value: number) {
  return `${numberFormatter.format(value)} руб`;
}

function parseNumber(raw: string) {
  const normalized = raw.replace(/\s+/g, "").replace(/,/g, ".");

  if (!normalized) {
    return Number.NaN;
  }

  return Number(normalized);
}

function buildExpenseForm(item?: ExpenseItem): ExpenseForm {
  if (!item) {
    return {
      category: categoryOptions[0],
      expenseType: expenseTypeOptions[0],
      description: "",
      monthlyAmount: "",
    };
  }

  return {
    category: item.category,
    expenseType: item.expenseType,
    description: item.description,
    monthlyAmount: String(item.monthlyAmountRub),
  };
}

function buildCreditForm(item?: CreditItem): CreditForm {
  if (!item) {
    return {
      bank: "",
      loanAmount: "",
      termMonths: "",
      monthlyPayment: "",
      interestRate: "",
    };
  }

  return {
    bank: item.bank,
    loanAmount: String(item.loanAmountRub),
    termMonths: String(item.termMonths),
    monthlyPayment: String(item.monthlyPaymentRub),
    interestRate: item.interestRate ? String(item.interestRate) : "",
  };
}

function getRecommendation(totalExpensesRub: number, incomeRub: number) {
  const ratio = incomeRub > 0 ? totalExpensesRub / incomeRub : 0;

  if (ratio <= 0.25) {
    return "Учитывая доходы и расходы, вы в топе финансовой дисциплины: нагрузка по расходам очень низкая.";
  }

  if (ratio <= 0.45) {
    return "Баланс хороший. Чтобы увеличить запас, попробуйте сократить 1-2 необязательные статьи расходов.";
  }

  return "Расходная нагрузка заметная. Стоит оптимизировать подписки и крупные обязательные платежи.";
}

export function ExpensesPage() {
  const [expenses, setExpenses] = useState<ExpenseItem[]>(initialExpenses);
  const [credits, setCredits] = useState<CreditItem[]>(initialCredits);
  const [sheet, setSheet] = useState<SheetState>(null);

  const [expenseForm, setExpenseForm] = useState<ExpenseForm>(buildExpenseForm());
  const [creditForm, setCreditForm] = useState<CreditForm>(buildCreditForm());
  const [errors, setErrors] = useState<FormErrors>({});

  const isSheetOpen = sheet !== null;
  const isExpenseSheet = sheet?.kind === "expense";
  const isCreditSheet = sheet?.kind === "credit";

  const incomeRub = financeMetrics.incomeRub;

  const totalExpensesRub = useMemo(() => {
    const expensesRub = expenses.reduce((sum, expense) => sum + expense.monthlyAmountRub, 0);
    const creditsRub = credits.reduce((sum, credit) => sum + credit.monthlyPaymentRub, 0);

    return expensesRub + creditsRub;
  }, [credits, expenses]);

  const recommendationText = useMemo(() => getRecommendation(totalExpensesRub, incomeRub), [incomeRub, totalExpensesRub]);

  function closeSheet() {
    setSheet(null);
    setErrors({});
  }

  function openCreateExpenseSheet() {
    setExpenseForm(buildExpenseForm());
    setErrors({});
    setSheet({ kind: "expense", mode: "create" });
  }

  function openEditExpenseSheet(expenseId: string) {
    const item = expenses.find((entry) => entry.id === expenseId);

    if (!item) {
      return;
    }

    setExpenseForm(buildExpenseForm(item));
    setErrors({});
    setSheet({ kind: "expense", mode: "edit", id: expenseId });
  }

  function openCreateCreditSheet() {
    setCreditForm(buildCreditForm());
    setErrors({});
    setSheet({ kind: "credit", mode: "create" });
  }

  function openEditCreditSheet(creditId: string) {
    const item = credits.find((entry) => entry.id === creditId);

    if (!item) {
      return;
    }

    setCreditForm(buildCreditForm(item));
    setErrors({});
    setSheet({ kind: "credit", mode: "edit", id: creditId });
  }

  function validateExpenseForm() {
    const nextErrors: FormErrors = {};

    if (!expenseForm.category.trim()) {
      nextErrors.category = "Выберите категорию";
    }

    if (!expenseForm.expenseType.trim()) {
      nextErrors.expenseType = "Выберите тип расхода";
    }

    if (!expenseForm.description.trim()) {
      nextErrors.description = "Введите описание";
    }

    const monthlyAmount = parseNumber(expenseForm.monthlyAmount);

    if (!Number.isFinite(monthlyAmount) || monthlyAmount <= 0) {
      nextErrors.monthlyAmount = "Введите сумму больше нуля";
    }

    return {
      isValid: Object.keys(nextErrors).length === 0,
      errors: nextErrors,
      monthlyAmount,
    };
  }

  function validateCreditForm() {
    const nextErrors: FormErrors = {};

    if (!creditForm.bank.trim()) {
      nextErrors.bank = "Введите название банка";
    }

    const loanAmount = parseNumber(creditForm.loanAmount);

    if (!Number.isFinite(loanAmount) || loanAmount <= 0) {
      nextErrors.loanAmount = "Введите сумму кредита больше нуля";
    }

    const termMonths = parseNumber(creditForm.termMonths);

    if (!Number.isFinite(termMonths) || termMonths <= 0 || !Number.isInteger(termMonths)) {
      nextErrors.termMonths = "Введите срок в месяцах";
    }

    const monthlyPayment = parseNumber(creditForm.monthlyPayment);

    if (!Number.isFinite(monthlyPayment) || monthlyPayment <= 0) {
      nextErrors.monthlyPayment = "Введите ежемесячный платёж";
    }

    const hasRate = creditForm.interestRate.trim().length > 0;
    const interestRate = hasRate ? parseNumber(creditForm.interestRate) : undefined;

    if (hasRate && (!Number.isFinite(interestRate) || (interestRate ?? 0) < 0)) {
      nextErrors.interestRate = "Ставка должна быть неотрицательной";
    }

    return {
      isValid: Object.keys(nextErrors).length === 0,
      errors: nextErrors,
      loanAmount,
      termMonths,
      monthlyPayment,
      interestRate,
    };
  }

  function submitExpense() {
    const validation = validateExpenseForm();

    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }

    if (sheet?.kind !== "expense") {
      return;
    }

    if (sheet.mode === "create") {
      setExpenses((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          category: expenseForm.category,
          expenseType: expenseForm.expenseType,
          description: expenseForm.description.trim(),
          monthlyAmountRub: Math.round(validation.monthlyAmount),
        },
      ]);
    } else {
      setExpenses((current) =>
        current.map((item) => {
          if (item.id !== sheet.id) {
            return item;
          }

          return {
            ...item,
            category: expenseForm.category,
            expenseType: expenseForm.expenseType,
            description: expenseForm.description.trim(),
            monthlyAmountRub: Math.round(validation.monthlyAmount),
          };
        }),
      );
    }

    closeSheet();
  }

  function submitCredit() {
    const validation = validateCreditForm();

    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }

    if (sheet?.kind !== "credit") {
      return;
    }

    if (sheet.mode === "create") {
      setCredits((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          bank: creditForm.bank.trim(),
          loanAmountRub: Math.round(validation.loanAmount),
          termMonths: Math.round(validation.termMonths),
          monthlyPaymentRub: Math.round(validation.monthlyPayment),
          interestRate: validation.interestRate,
        },
      ]);
    } else {
      setCredits((current) =>
        current.map((item) => {
          if (item.id !== sheet.id) {
            return item;
          }

          return {
            ...item,
            bank: creditForm.bank.trim(),
            loanAmountRub: Math.round(validation.loanAmount),
            termMonths: Math.round(validation.termMonths),
            monthlyPaymentRub: Math.round(validation.monthlyPayment),
            interestRate: validation.interestRate,
          };
        }),
      );
    }

    closeSheet();
  }

  function deleteExpense() {
    if (sheet?.kind !== "expense" || sheet.mode !== "edit") {
      return;
    }

    setExpenses((current) => current.filter((item) => item.id !== sheet.id));
    closeSheet();
  }

  function deleteCredit() {
    if (sheet?.kind !== "credit" || sheet.mode !== "edit") {
      return;
    }

    setCredits((current) => current.filter((item) => item.id !== sheet.id));
    closeSheet();
  }

  return (
    <main className={styles.financeScreen}>
      <div className={clsx(styles.contentWrap, isSheetOpen && styles.expensesContentDimmed)}>
        <FinanceHeader title="Расходы" leftHref={financeRoutes.home} leftIcon="back" prizeHref={financeRoutes.achievements} logoutHref="/" />

        <section className={styles.expensesSummaryCard}>
          <div>
            <p className={styles.expensesSummaryCaption}>Ваш расход мес</p>
            <p className={styles.expensesSummaryValue}>
              <strong>{numberFormatter.format(totalExpensesRub)}</strong>
              <span>руб</span>
            </p>
          </div>

          <div className={styles.expensesIncomePill}>
            <p className={styles.expensesIncomeLabel}>Доход</p>
            <p className={styles.expensesIncomeValue}>{formatRub(incomeRub)}</p>
          </div>
        </section>

        <section className={styles.expensesSection}>
          <div className={styles.expensesSectionHeader}>
            <h2 className={styles.expensesSectionTitle}>Постоянные расходы</h2>
            <button className={styles.expensesAddButton} type="button" onClick={openCreateExpenseSheet} aria-label="Добавить расход">
              +
            </button>
          </div>

          {expenses.length ? (
            <div className={styles.expensesList}>
              {expenses.map((expense) => (
                <button className={styles.expenseRowCard} type="button" key={expense.id} onClick={() => openEditExpenseSheet(expense.id)}>
                  <span>{expense.description}</span>
                  <span>
                    <strong>{numberFormatter.format(expense.monthlyAmountRub)}</strong> руб
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className={styles.expensesEmptyState}>Пока нет расходов. Нажмите «+», чтобы добавить первый пункт.</p>
          )}
        </section>

        <section className={styles.expensesSection}>
          <div className={styles.expensesSectionHeader}>
            <h2 className={styles.expensesSectionTitle}>Кредиты</h2>
            <button className={styles.expensesAddButton} type="button" onClick={openCreateCreditSheet} aria-label="Добавить кредит">
              +
            </button>
          </div>

          {credits.length ? (
            <div className={styles.expensesList}>
              {credits.map((credit) => (
                <button className={styles.creditCard} type="button" key={credit.id} onClick={() => openEditCreditSheet(credit.id)}>
                  <div className={styles.creditCardTop}>
                    <span>Кредит {credit.bank}</span>
                    <span>
                      <strong>{numberFormatter.format(credit.loanAmountRub)}</strong> руб
                    </span>
                  </div>

                  <div className={styles.creditCardDivider} />

                  <div className={styles.creditCardBottom}>
                    <span>
                      <strong>{numberFormatter.format(credit.monthlyPaymentRub)}</strong> руб в мес
                    </span>
                    <span>Осталось {credit.termMonths} мес</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <p className={styles.expensesEmptyState}>Кредиты не добавлены. Нажмите «+», чтобы указать кредитную нагрузку.</p>
          )}
        </section>

        <section className={styles.expensesSection}>
          <h2 className={styles.expensesSectionTitle}>Рекомендации</h2>
          <div className={styles.expensesRecommendationCard}>{recommendationText}</div>
        </section>
      </div>

      <BottomSheetModal
        isOpen={isSheetOpen}
        onClose={closeSheet}
        ariaLabel={isExpenseSheet ? "Добавить расход" : "Добавить кредит"}
        title={
          isExpenseSheet ? (sheet?.mode === "edit" ? "Редактировать расход" : "Добавить расход") : sheet?.mode === "edit" ? "Редактировать кредит" : "Добавить кредит"
        }
        backdropClassName={styles.expensesSheetBackdrop}
        sheetClassName={styles.expensesSheet}
        handleClassName={styles.expensesSheetHandle}
        titleClassName={styles.expensesSheetTitle}
      >
        {isExpenseSheet ? (
          <form
            className={styles.expenseSheetForm}
            onSubmit={(event) => {
              event.preventDefault();
              submitExpense();
            }}
          >
            <div className={styles.expenseSheetSelectRow}>
              <label className={styles.expenseSheetLabel} htmlFor="expense-category">
                Категория
              </label>
              <select
                id="expense-category"
                className={styles.expenseSheetSelect}
                value={expenseForm.category}
                onChange={(event) => setExpenseForm((current) => ({ ...current, category: event.target.value }))}
              >
                {categoryOptions.map((option) => (
                  <option value={option} key={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            {errors.category ? <p className={styles.formError}>{errors.category}</p> : null}

            <div className={styles.expenseSheetSelectRow}>
              <label className={styles.expenseSheetLabel} htmlFor="expense-type">
                Тип расхода
              </label>
              <select
                id="expense-type"
                className={styles.expenseSheetSelect}
                value={expenseForm.expenseType}
                onChange={(event) => setExpenseForm((current) => ({ ...current, expenseType: event.target.value as ExpenseType }))}
              >
                {expenseTypeOptions.map((option) => (
                  <option value={option} key={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            {errors.expenseType ? <p className={styles.formError}>{errors.expenseType}</p> : null}

            <div className={styles.expenseSheetInputGroup}>
              <label className={styles.expenseSheetInputLabel} htmlFor="expense-description">
                Описание
              </label>
              <input
                id="expense-description"
                className={styles.expenseSheetInput}
                value={expenseForm.description}
                onChange={(event) => setExpenseForm((current) => ({ ...current, description: event.target.value }))}
              />

              <div className={styles.expenseSheetInputDivider} />

              <label className={styles.expenseSheetInputLabel} htmlFor="expense-monthly-amount">
                Сумма в мес
              </label>
              <input
                id="expense-monthly-amount"
                className={styles.expenseSheetInput}
                inputMode="numeric"
                value={expenseForm.monthlyAmount}
                onChange={(event) => setExpenseForm((current) => ({ ...current, monthlyAmount: event.target.value }))}
              />
            </div>
            {errors.description ? <p className={styles.formError}>{errors.description}</p> : null}
            {errors.monthlyAmount ? <p className={styles.formError}>{errors.monthlyAmount}</p> : null}

            <div className={styles.sheetActions}>
              {sheet?.mode === "edit" ? (
                <button className={styles.sheetDeleteButton} type="button" onClick={deleteExpense}>
                  <Trash2 size={16} /> Удалить
                </button>
              ) : null}
              <button className={styles.sheetSaveButton} type="submit">
                {sheet?.mode === "edit" ? "Сохранить" : "Добавить"}
              </button>
            </div>
          </form>
        ) : null}

        {isCreditSheet ? (
          <form
            className={styles.expenseSheetForm}
            onSubmit={(event) => {
              event.preventDefault();
              submitCredit();
            }}
          >
            <div className={styles.expenseSheetInputGroup}>
              <label className={styles.expenseSheetInputLabel} htmlFor="credit-bank">
                Банк где был взят кредит
              </label>
              <input
                id="credit-bank"
                className={styles.expenseSheetInput}
                value={creditForm.bank}
                onChange={(event) => setCreditForm((current) => ({ ...current, bank: event.target.value }))}
              />

              <div className={styles.expenseSheetInputDivider} />

              <label className={styles.expenseSheetInputLabel} htmlFor="credit-loan-amount">
                Сумма кредита
              </label>
              <input
                id="credit-loan-amount"
                className={styles.expenseSheetInput}
                inputMode="numeric"
                value={creditForm.loanAmount}
                onChange={(event) => setCreditForm((current) => ({ ...current, loanAmount: event.target.value }))}
              />

              <div className={styles.expenseSheetInputDivider} />

              <label className={styles.expenseSheetInputLabel} htmlFor="credit-term-months">
                Срок
              </label>
              <input
                id="credit-term-months"
                className={styles.expenseSheetInput}
                inputMode="numeric"
                value={creditForm.termMonths}
                onChange={(event) => setCreditForm((current) => ({ ...current, termMonths: event.target.value }))}
              />

              <div className={styles.expenseSheetInputDivider} />

              <label className={styles.expenseSheetInputLabel} htmlFor="credit-monthly-payment">
                Ежемесячный платёж
              </label>
              <input
                id="credit-monthly-payment"
                className={styles.expenseSheetInput}
                inputMode="numeric"
                value={creditForm.monthlyPayment}
                onChange={(event) => setCreditForm((current) => ({ ...current, monthlyPayment: event.target.value }))}
              />

              <div className={styles.expenseSheetInputDivider} />

              <label className={styles.expenseSheetInputLabel} htmlFor="credit-interest-rate">
                Процентная ставка - опционально
              </label>
              <input
                id="credit-interest-rate"
                className={styles.expenseSheetInput}
                inputMode="decimal"
                value={creditForm.interestRate}
                onChange={(event) => setCreditForm((current) => ({ ...current, interestRate: event.target.value }))}
              />
            </div>

            {errors.bank ? <p className={styles.formError}>{errors.bank}</p> : null}
            {errors.loanAmount ? <p className={styles.formError}>{errors.loanAmount}</p> : null}
            {errors.termMonths ? <p className={styles.formError}>{errors.termMonths}</p> : null}
            {errors.monthlyPayment ? <p className={styles.formError}>{errors.monthlyPayment}</p> : null}
            {errors.interestRate ? <p className={styles.formError}>{errors.interestRate}</p> : null}

            <div className={styles.sheetActions}>
              {sheet?.mode === "edit" ? (
                <button className={styles.sheetDeleteButton} type="button" onClick={deleteCredit}>
                  <Trash2 size={16} /> Удалить
                </button>
              ) : null}
              <button className={styles.sheetSaveButton} type="submit">
                {sheet?.mode === "edit" ? "Сохранить" : "Добавить"}
              </button>
            </div>
          </form>
        ) : null}
      </BottomSheetModal>
    </main>
  );
}
