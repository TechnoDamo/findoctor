"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { BottomSheetModal } from "@/components/BottomSheetModal";
import { FinanceHeader } from "@/components/FinanceHeader";
import { financeSectionsBySlug } from "@/lib/financeSections";
import { numberFormatter } from "@/lib/financeData";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./day-spending-page.module.css";

type OperationDirection = "expense" | "income";
type OperationMode = "create" | "edit";
type PickerKind = "category" | "type";

type DayOperation = {
  id: string;
  direction: OperationDirection;
  category: string;
  type: string;
  description: string;
  amountRub: number;
};

type DaySpendingSheetMode = "expense" | "income";

type DaySpendingPageProps = {
  initialMode: DaySpendingSheetMode;
  initialOpen?: boolean;
};

const categoryOptions = ["Дети", "Подписки", "Жилье", "Транспорт", "Здоровье", "Еда", "Развлечения", "Другое"];
const expenseTypeOptions = ["Обязательные расходы", "Необязательные расходы"];
const incomeTypeOptions = ["Постоянный доход", "Непостоянный доход"];

const initialOperations: DayOperation[] = [
  {
    id: "day-expense-1",
    direction: "expense",
    category: "Дети",
    type: "Обязательные расходы",
    description: "Детям на сладкое",
    amountRub: 2000,
  },
  {
    id: "day-expense-2",
    direction: "expense",
    category: "Подписки",
    type: "Необязательные расходы",
    description: "Подписки на GPT",
    amountRub: 7000,
  },
  {
    id: "day-income-1",
    direction: "income",
    category: "Подписки",
    type: "Постоянный доход",
    description: "Подписки на GPT",
    amountRub: 7000,
  },
  {
    id: "day-income-2",
    direction: "income",
    category: "Подписки",
    type: "Непостоянный доход",
    description: "Подписки на GPT",
    amountRub: 7000,
  },
];

function parseRubAmount(rawValue?: string) {
  if (!rawValue) {
    return 0;
  }

  const digitsOnly = rawValue.replace(/[^\d]/g, "");
  const value = Number.parseInt(digitsOnly, 10);

  return Number.isFinite(value) ? value : 0;
}

function formatRub(value: number) {
  return numberFormatter.format(Math.max(0, Math.round(value)));
}

export function DaySpendingPage({ initialMode, initialOpen = false }: DaySpendingPageProps) {
  const [reminderEnabled, setReminderEnabled] = useState(true);
  const [operations, setOperations] = useState<DayOperation[]>(initialOperations);

  const [sheetMode, setSheetMode] = useState<DaySpendingSheetMode>(initialMode);
  const [sheetOpen, setSheetOpen] = useState(initialOpen);
  const [sheetOperationMode, setSheetOperationMode] = useState<OperationMode>("create");
  const [editingOperationId, setEditingOperationId] = useState<string | null>(null);

  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerKind, setPickerKind] = useState<PickerKind>("category");

  const [selectedCategory, setSelectedCategory] = useState(categoryOptions[0]);
  const [selectedType, setSelectedType] = useState(expenseTypeOptions[0]);
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");

  const dayLimitRub = useMemo(() => {
    const fromSection = financeSectionsBySlug["day_spending_page"]?.amount;
    return parseRubAmount(fromSection);
  }, []);

  const expenseOperations = useMemo(() => operations.filter((operation) => operation.direction === "expense"), [operations]);
  const incomeOperations = useMemo(() => operations.filter((operation) => operation.direction === "income"), [operations]);

  const todayExpensesRub = useMemo(
    () => expenseOperations.reduce((sum, operation) => sum + operation.amountRub, 0),
    [expenseOperations],
  );

  const remainderRub = Math.max(dayLimitRub - todayExpensesRub, 0);

  const currentTypeOptions = sheetMode === "expense" ? expenseTypeOptions : incomeTypeOptions;
  const sheetTitle =
    sheetOperationMode === "edit"
      ? sheetMode === "expense"
        ? "Редактировать расход"
        : "Редактировать доход"
      : sheetMode === "expense"
        ? "Расходы на день"
        : "Доходы на день";

  const pickerTitle = pickerKind === "category" ? "Выберите категорию" : sheetMode === "expense" ? "Выберите тип расхода" : "Выберите тип дохода";

  function closeMainSheet() {
    setSheetOpen(false);
    setEditingOperationId(null);
  }

  function openCreateSheet(direction: OperationDirection) {
    setSheetMode(direction);
    setSheetOperationMode("create");
    setEditingOperationId(null);
    setSelectedCategory(categoryOptions[0]);
    setSelectedType((direction === "expense" ? expenseTypeOptions : incomeTypeOptions)[0]);
    setDescription("");
    setAmount("");
    setSheetOpen(true);
  }

  function openEditSheet(operation: DayOperation) {
    setSheetMode(operation.direction);
    setSheetOperationMode("edit");
    setEditingOperationId(operation.id);
    setSelectedCategory(operation.category);
    setSelectedType(operation.type);
    setDescription(operation.description);
    setAmount(String(operation.amountRub));
    setSheetOpen(true);
  }

  function openPicker(kind: PickerKind) {
    setPickerKind(kind);
    setPickerOpen(true);
  }

  function closePicker() {
    setPickerOpen(false);
  }

  function applyOption(option: string) {
    if (pickerKind === "category") {
      setSelectedCategory(option);
    } else {
      setSelectedType(option);
    }

    closePicker();
  }

  function saveOperation() {
    const normalizedDescription = description.trim();
    const parsedAmount = Number.parseInt(amount.replace(/[^\d]/g, ""), 10);

    if (!normalizedDescription || !Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      return;
    }

    if (sheetOperationMode === "edit" && editingOperationId) {
      setOperations((current) =>
        current.map((operation) =>
          operation.id === editingOperationId
            ? {
                ...operation,
                direction: sheetMode,
                category: selectedCategory,
                type: selectedType,
                description: normalizedDescription,
                amountRub: parsedAmount,
              }
            : operation,
        ),
      );
      closeMainSheet();
      return;
    }

    const newOperation: DayOperation = {
      id: `day-operation-${crypto.randomUUID()}`,
      direction: sheetMode,
      category: selectedCategory,
      type: selectedType,
      description: normalizedDescription,
      amountRub: parsedAmount,
    };

    setOperations((current) => [newOperation, ...current]);
    closeMainSheet();
  }

  const pickerOptions = pickerKind === "category" ? categoryOptions : currentTypeOptions;

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title={"Траты\nна день"}
          leftHref={financeRoutes.home}
          leftIcon="back"
          prizeHref={financeRoutes.achievements}
          logoutHref="/login"
          headerClassName={styles.header}
          titleClassName={styles.headerTitle}
        />

        <section className={styles.summaryCard} aria-label="Сводка трат на день">
          <p className={styles.summaryLabel}>Остаток на сегодня</p>
          <p className={styles.summaryValue}>
            <strong>{formatRub(remainderRub)}</strong>
            <span>руб</span>
          </p>

          <div className={styles.summaryDivider} aria-hidden="true" />

          <p className={styles.summaryLabel}>Лимит на день</p>
          <p className={styles.summaryValue}>
            <strong>{formatRub(dayLimitRub)}</strong>
            <span>руб</span>
          </p>
        </section>

        <section className={styles.reminderCard} aria-label="Напоминание о заполнении">
          <p className={styles.reminderLabel}>Напоминать о заполнении</p>

          <button
            type="button"
            role="switch"
            aria-checked={reminderEnabled}
            className={styles.reminderSwitch}
            onClick={() => setReminderEnabled((current) => !current)}
          >
            <span className={styles.reminderSwitchThumb} aria-hidden="true" />
          </button>
        </section>

        <section className={styles.recommendationSection} aria-label="Рекомендации">
          <h2 className={styles.sectionTitle}>Рекомендации</h2>

          <article className={styles.recommendationCard}>
            <p className={styles.recommendationText}>
              На этой неделе предлагаю уменьшить лимит на день до 1 500 руб, так как это позволит добиться цели на 4 мес быстрее
            </p>

            <Link className={styles.detailsLink} href={financeRoutes.consultant}>
              Подробнее
            </Link>
          </article>
        </section>

        <section className={styles.operationsSection} aria-label="Расходы на сегодня">
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Расходы на сегодня</h2>
            <button type="button" className={styles.addButton} onClick={() => openCreateSheet("expense")} aria-label="Добавить расход">
              +
            </button>
          </div>

          <div className={styles.operationsList}>
            {expenseOperations.map((operation) => (
              <button key={operation.id} type="button" className={styles.operationCard} onClick={() => openEditSheet(operation)}>
                <div className={styles.operationText}>
                  <p className={styles.operationType}>{operation.type}</p>
                  <p className={styles.operationName}>{operation.description}</p>
                </div>
                <p className={styles.operationAmount}>
                  <strong>{formatRub(operation.amountRub)}</strong>
                  <span>руб</span>
                </p>
              </button>
            ))}
          </div>
        </section>

        <section className={styles.operationsSectionIncome} aria-label="Доходы на сегодня">
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Доходы на сегодня</h2>
            <button type="button" className={styles.addButton} onClick={() => openCreateSheet("income")} aria-label="Добавить доход">
              +
            </button>
          </div>

          <div className={styles.operationsList}>
            {incomeOperations.map((operation) => (
              <button key={operation.id} type="button" className={styles.operationCard} onClick={() => openEditSheet(operation)}>
                <div className={styles.operationText}>
                  <p className={styles.operationType}>{operation.type}</p>
                  <p className={styles.operationName}>{operation.description}</p>
                </div>
                <p className={styles.operationAmount}>
                  <strong>{formatRub(operation.amountRub)}</strong>
                  <span>руб</span>
                </p>
              </button>
            ))}
          </div>
        </section>
      </div>

      <BottomSheetModal
        isOpen={sheetOpen}
        onClose={closeMainSheet}
        ariaLabel={sheetTitle}
        title={sheetTitle}
        backdropClassName={styles.backdrop}
        sheetClassName={styles.sheet}
        handleClassName={styles.sheetHandle}
        titleClassName={styles.sheetTitle}
      >
        <button type="button" className={styles.selectPill} onClick={() => openPicker("category")}>
          <span className={styles.selectLabel}>Категория</span>
          <span className={styles.selectValue}>{selectedCategory}</span>
        </button>

        <button type="button" className={styles.selectPill} onClick={() => openPicker("type")}>
          <span className={styles.selectLabel}>{sheetMode === "expense" ? "Тип расхода" : "Тип дохода"}</span>
          <span className={styles.selectValue}>{selectedType}</span>
        </button>

        <section className={styles.inputCard} aria-label="Описание и сумма">
          <input
            className={styles.textInput}
            type="text"
            placeholder="Описание"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            aria-label="Описание"
          />

          <div className={styles.inputDivider} aria-hidden="true" />

          <input
            className={styles.textInput}
            type="text"
            inputMode="numeric"
            placeholder="Сумма"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            aria-label="Сумма"
          />
        </section>

        <button type="button" className={styles.saveButton} onClick={saveOperation}>
          {sheetOperationMode === "edit" ? "Сохранить изменения" : "Сохранить операцию"}
        </button>
      </BottomSheetModal>

      <BottomSheetModal
        isOpen={pickerOpen}
        onClose={closePicker}
        ariaLabel={pickerTitle}
        title={pickerTitle}
        backdropClassName={styles.backdrop}
        sheetClassName={styles.pickerSheet}
        handleClassName={styles.sheetHandle}
        titleClassName={styles.sheetTitle}
      >
        <div className={styles.optionList}>
          {pickerOptions.map((option) => (
            <button key={option} type="button" className={styles.optionButton} onClick={() => applyOption(option)}>
              {option}
            </button>
          ))}
        </div>
      </BottomSheetModal>
    </main>
  );
}
