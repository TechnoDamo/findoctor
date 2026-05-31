"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { BottomSheetModal } from "@/components/BottomSheetModal";
import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./credit-traffic-page.module.css";

type CreditTrafficModalKind = "chat" | "add-credit";
type CreditRisk = "safe" | "caution" | "danger";

type CreditCalculatorForm = {
  loanAmount: string;
  term: string;
  monthlyPayment: string;
  interestRate: string;
  loanPurpose: string;
  incomeStability: string;
};

type CreditCalculationResult = {
  status: CreditRisk;
  statusText: string;
  recommendation: string;
  estimatedPayment: number;
  enteredPayment: number;
  totalOverpayment: number;
};

type CreditCardData = {
  bankName: string;
  amountRub: number;
  monthlyPaymentRub: number;
  monthsLeft: number;
};

type CreditEditForm = {
  bankName: string;
  amountRub: string;
  monthlyPaymentRub: string;
  monthsLeft: string;
};

const mockLoadValue = 24;

const markerPosition = Math.max(0, Math.min(100, mockLoadValue));

const modalCopy: Record<CreditTrafficModalKind, { title: string; description: string }> = {
  chat: {
    title: "Продолжить в чате",
    description: "Здесь будет переход в чат с консультантом по кредитной нагрузке.",
  },
  "add-credit": {
    title: "Добавить кредит",
    description: "Здесь будет bottom sheet для добавления нового кредита.",
  },
};

const creditPurposeOptions = ["техника", "ремонт", "автомобиль", "лечение", "обучение", "закрыть другой долг", "бизнес", "другое"];

const incomeStabilityOptions = [
  "стабильная зарплата",
  "доход меняется от месяца к месяцу",
  "фриланс / самозанятость",
  "сейчас есть риск потери дохода",
];

const initialCreditForm: CreditCalculatorForm = {
  loanAmount: "",
  term: "",
  monthlyPayment: "",
  interestRate: "",
  loanPurpose: "",
  incomeStability: "",
};

const initialCreditCard: CreditCardData = {
  bankName: "Кредит СберБанк",
  amountRub: 450000,
  monthlyPaymentRub: 7000,
  monthsLeft: 46,
};

function parseNumber(value: string) {
  const normalized = value.replace(/\s+/g, "").replace(",", ".");
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : Number.NaN;
}

function formatRub(value: number) {
  return new Intl.NumberFormat("ru-RU").format(Math.round(value));
}

function evaluateCreditCalculation(form: CreditCalculatorForm): CreditCalculationResult {
  const loanAmount = parseNumber(form.loanAmount);
  const termMonths = parseNumber(form.term);
  const monthlyPayment = parseNumber(form.monthlyPayment);
  const interestRate = form.interestRate.trim() ? parseNumber(form.interestRate) : 18;

  const monthlyRate = interestRate > 0 ? interestRate / 1200 : 0;
  const estimatedPayment =
    monthlyRate > 0 ? (loanAmount * monthlyRate) / (1 - Math.pow(1 + monthlyRate, -termMonths)) : loanAmount / Math.max(termMonths, 1);

  const totalOverpayment = Math.max(monthlyPayment * termMonths - loanAmount, 0);

  let riskScore = 0;

  if (interestRate >= 28) {
    riskScore += 3;
  } else if (interestRate >= 20) {
    riskScore += 2;
  } else if (interestRate >= 14) {
    riskScore += 1;
  }

  if (termMonths >= 96) {
    riskScore += 2;
  } else if (termMonths >= 60) {
    riskScore += 1;
  }

  const paymentCoverage = monthlyPayment / Math.max(estimatedPayment, 1);
  if (paymentCoverage < 0.9) {
    riskScore += 3;
  } else if (paymentCoverage < 1) {
    riskScore += 2;
  } else if (paymentCoverage < 1.1) {
    riskScore += 1;
  }

  if (form.incomeStability === "доход меняется от месяца к месяцу") {
    riskScore += 1;
  } else if (form.incomeStability === "фриланс / самозанятость") {
    riskScore += 2;
  } else if (form.incomeStability === "сейчас есть риск потери дохода") {
    riskScore += 3;
  }

  if (form.loanPurpose === "закрыть другой долг" || form.loanPurpose === "бизнес") {
    riskScore += 1;
  }

  let status: CreditRisk = "safe";
  if (riskScore >= 7) {
    status = "danger";
  } else if (riskScore >= 4) {
    status = "caution";
  }

  if (status === "safe") {
    return {
      status,
      statusText: "Можно",
      recommendation: `Параметры кредита выглядят устойчиво. Рекомендуемый платеж около ${formatRub(estimatedPayment)} руб/мес и лучше держать финансовый запас минимум на 3 месяца.`,
      estimatedPayment,
      enteredPayment: monthlyPayment,
      totalOverpayment,
    };
  }

  if (status === "caution") {
    return {
      status,
      statusText: "Осторожно",
      recommendation: `Есть повышенная нагрузка. Лучше снизить сумму кредита или увеличить срок так, чтобы платеж был ближе к ${formatRub(estimatedPayment)} руб/мес.`,
      estimatedPayment,
      enteredPayment: monthlyPayment,
      totalOverpayment,
    };
  }

  return {
    status,
    statusText: "Не стоит",
    recommendation: `Параметры займа слишком рискованные. Рекомендуется отложить кредит и уменьшить долговую нагрузку перед новым оформлением.`,
    estimatedPayment,
    enteredPayment: monthlyPayment,
    totalOverpayment,
  };
}

export function CreditTrafficPage() {
  const router = useRouter();
  const [activeModal, setActiveModal] = useState<CreditTrafficModalKind | null>(null);
  const [creditCard, setCreditCard] = useState<CreditCardData>(initialCreditCard);
  const [isEditCreditOpen, setIsEditCreditOpen] = useState(false);
  const [editCreditForm, setEditCreditForm] = useState<CreditEditForm>({
    bankName: initialCreditCard.bankName,
    amountRub: String(initialCreditCard.amountRub),
    monthlyPaymentRub: String(initialCreditCard.monthlyPaymentRub),
    monthsLeft: String(initialCreditCard.monthsLeft),
  });
  const [editCreditErrors, setEditCreditErrors] = useState<Partial<Record<keyof CreditEditForm, string>>>({});

  const [isCreditCalculatorOpen, setIsCreditCalculatorOpen] = useState(false);
  const [isCreditResultOpen, setIsCreditResultOpen] = useState(false);
  const [creditForm, setCreditForm] = useState<CreditCalculatorForm>(initialCreditForm);
  const [creditErrors, setCreditErrors] = useState<Partial<Record<keyof CreditCalculatorForm, string>>>({});
  const [creditResult, setCreditResult] = useState<CreditCalculationResult | null>(null);

  function openCreditCalculator() {
    setIsCreditCalculatorOpen(true);
    setIsCreditResultOpen(false);
    setCreditErrors({});
    setCreditResult(null);
  }

  function closeCreditCalculator() {
    setIsCreditCalculatorOpen(false);
  }

  function closeCreditResult() {
    setIsCreditResultOpen(false);
  }

  function openEditCreditModal() {
    setEditCreditForm({
      bankName: creditCard.bankName,
      amountRub: String(creditCard.amountRub),
      monthlyPaymentRub: String(creditCard.monthlyPaymentRub),
      monthsLeft: String(creditCard.monthsLeft),
    });
    setEditCreditErrors({});
    setIsEditCreditOpen(true);
  }

  function closeEditCreditModal() {
    setIsEditCreditOpen(false);
  }

  function updateEditCreditField(field: keyof CreditEditForm, value: string) {
    setEditCreditForm((current) => ({ ...current, [field]: value }));
    setEditCreditErrors((current) => ({ ...current, [field]: undefined }));
  }

  function validateCreditEditForm(form: CreditEditForm) {
    const nextErrors: Partial<Record<keyof CreditEditForm, string>> = {};

    if (!form.bankName.trim()) {
      nextErrors.bankName = "Введите название кредита";
    }

    const amount = parseNumber(form.amountRub);
    if (!(amount > 0)) {
      nextErrors.amountRub = "Введите сумму кредита больше нуля";
    }

    const monthlyPayment = parseNumber(form.monthlyPaymentRub);
    if (!(monthlyPayment > 0)) {
      nextErrors.monthlyPaymentRub = "Введите платеж больше нуля";
    }

    const monthsLeft = Number.parseInt(form.monthsLeft.replace(/[^\d]/g, ""), 10);
    if (!(monthsLeft > 0)) {
      nextErrors.monthsLeft = "Введите оставшийся срок больше нуля";
    }

    return nextErrors;
  }

  function handleSaveCreditEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validateCreditEditForm(editCreditForm);
    setEditCreditErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    const amountRub = parseNumber(editCreditForm.amountRub);
    const monthlyPaymentRub = parseNumber(editCreditForm.monthlyPaymentRub);
    const monthsLeft = Number.parseInt(editCreditForm.monthsLeft.replace(/[^\d]/g, ""), 10);

    setCreditCard({
      bankName: editCreditForm.bankName.trim(),
      amountRub: Math.round(amountRub),
      monthlyPaymentRub: Math.round(monthlyPaymentRub),
      monthsLeft,
    });
    setIsEditCreditOpen(false);
  }

  function updateFormField(field: keyof CreditCalculatorForm, value: string) {
    setCreditForm((current) => ({ ...current, [field]: value }));
    setCreditErrors((current) => ({ ...current, [field]: undefined }));
  }

  function validateCreditForm(form: CreditCalculatorForm) {
    const nextErrors: Partial<Record<keyof CreditCalculatorForm, string>> = {};

    const loanAmount = parseNumber(form.loanAmount);
    if (!(loanAmount > 0)) {
      nextErrors.loanAmount = "Введите сумму кредита больше нуля";
    }

    const term = parseNumber(form.term);
    if (!(term > 0)) {
      nextErrors.term = "Введите срок больше нуля";
    }

    const monthlyPayment = parseNumber(form.monthlyPayment);
    if (!(monthlyPayment > 0)) {
      nextErrors.monthlyPayment = "Введите ежемесячный платеж больше нуля";
    }

    if (form.interestRate.trim()) {
      const interestRate = parseNumber(form.interestRate);
      if (!(interestRate >= 0)) {
        nextErrors.interestRate = "Ставка должна быть пустой или не меньше нуля";
      }
    }

    if (!form.loanPurpose) {
      nextErrors.loanPurpose = "Выберите цель кредита";
    }

    if (!form.incomeStability) {
      nextErrors.incomeStability = "Выберите устойчивость дохода";
    }

    return nextErrors;
  }

  function handleCalculateCredit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validateCreditForm(creditForm);
    setCreditErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    const nextResult = evaluateCreditCalculation(creditForm);
    setCreditResult(nextResult);
    setIsCreditCalculatorOpen(false);
    setIsCreditResultOpen(true);
  }

  function handleOpenConsultantWithResult() {
    if (!creditResult) {
      router.push(financeRoutes.consultant);
      return;
    }

    const payload = [
      "Хочу обсудить расчет кредита.",
      `Статус: ${creditResult.statusText}.`,
      `Оценочный платеж: ${formatRub(creditResult.estimatedPayment)} руб/мес.`,
      `Мой платеж: ${formatRub(creditResult.enteredPayment)} руб/мес.`,
      `Рекомендация: ${creditResult.recommendation}`,
    ].join(" ");

    setIsCreditResultOpen(false);
    router.push(`${financeRoutes.consultant}?prefill=${encodeURIComponent(payload)}`);
  }

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title={"Кредитный\nСветофор"}
          leftHref={financeRoutes.home}
          leftIcon="back"
          prizeHref={financeRoutes.achievements}
          logoutHref="/login"
          titleClassName={styles.headerTitle}
        />

        <section className={styles.scoreCard} aria-label="Кредитная нагрузка">
          <h2 className={styles.scoreTitle}>Ваша кредитная нагрузка</h2>
          <div className={styles.progressBar} aria-hidden="true">
            <div className={styles.progressMarker} style={{ left: `${markerPosition}%` }}>
              <span className={styles.markerTriangle} />
              <span className={styles.markerValue}>{mockLoadValue}</span>
            </div>
          </div>
        </section>

        <section className={styles.recommendationCard} aria-label="Рекомендация">
          <p className={styles.recommendationText}>
            Ваша кредитная нагрузка - хорошая,
            <br />
            можете взять кредит максимум на
            <br />
            400 000 руб на 5 лет, больше нельзя
          </p>
          <button type="button" className={styles.chatButton} onClick={() => setActiveModal("chat")}>
            Продолжить в чате
          </button>
        </section>

        <button type="button" className={styles.calculateCreditButton} onClick={openCreditCalculator}>
          <span>Рассчитать кредит / займ</span>
          <ChevronRight size={24} strokeWidth={2.2} />
        </button>

        <section className={styles.creditsSection}>
          <div className={styles.creditsHeader}>
            <h2 className={styles.creditsTitle}>Кредиты</h2>
            <button type="button" className={styles.addCreditButton} onClick={() => setActiveModal("add-credit")} aria-label="Добавить кредит">
              +
            </button>
          </div>

          <button type="button" className={styles.creditCard} onClick={openEditCreditModal} aria-label={creditCard.bankName}>
            <div className={styles.creditTopRow}>
              <p className={styles.creditBank}>{creditCard.bankName}</p>
              <p className={styles.creditAmount}>
                <span className={styles.creditAmountValue}>{formatRub(creditCard.amountRub)}</span>
                <span className={styles.creditAmountUnit}> руб</span>
              </p>
            </div>

            <div className={styles.creditDivider} aria-hidden="true" />

            <div className={styles.creditBottomRow}>
              <p className={styles.creditPayment}>
                <span className={styles.creditPaymentValue}>{formatRub(creditCard.monthlyPaymentRub)}</span>
                <span className={styles.creditPaymentUnit}> руб в мес</span>
              </p>
              <p className={styles.creditLeftMonths}>Осталось {creditCard.monthsLeft} мес</p>
            </div>
          </button>
        </section>
      </div>

      <BottomSheetModal
        isOpen={activeModal !== null}
        onClose={() => setActiveModal(null)}
        ariaLabel={activeModal ? modalCopy[activeModal].title : "Модальное окно"}
        title={activeModal ? modalCopy[activeModal].title : undefined}
        backdropClassName={styles.modalBackdrop}
        sheetClassName={styles.modalSheet}
        handleClassName={styles.modalHandle}
        titleClassName={styles.modalTitle}
      >
        <p className={styles.modalDescription}>{activeModal ? modalCopy[activeModal].description : ""}</p>
        <button type="button" className={styles.modalCloseButton} onClick={() => setActiveModal(null)}>
          Закрыть
        </button>
      </BottomSheetModal>

      <BottomSheetModal
        isOpen={isEditCreditOpen}
        onClose={closeEditCreditModal}
        ariaLabel="Редактировать кредит"
        backdropClassName={styles.creditSheetBackdrop}
        sheetClassName={styles.creditSheet}
        handleClassName={styles.creditSheetHandle}
      >
        <h2 className={styles.sheetTitle}>Редактировать кредит</h2>

        <form className={styles.creditForm} onSubmit={handleSaveCreditEdit}>
          <div className={styles.inputGroupCard}>
            <input
              className={styles.inputRow}
              value={editCreditForm.bankName}
              onChange={(event) => updateEditCreditField("bankName", event.target.value)}
              placeholder="Название кредита"
              aria-label="Название кредита"
            />
            <input
              className={styles.inputRow}
              value={editCreditForm.amountRub}
              onChange={(event) => updateEditCreditField("amountRub", event.target.value)}
              placeholder="Сумма кредита"
              inputMode="decimal"
              aria-label="Сумма кредита"
            />
            <input
              className={styles.inputRow}
              value={editCreditForm.monthlyPaymentRub}
              onChange={(event) => updateEditCreditField("monthlyPaymentRub", event.target.value)}
              placeholder="Ежемесячный платеж"
              inputMode="decimal"
              aria-label="Ежемесячный платеж"
            />
            <input
              className={styles.inputRow}
              value={editCreditForm.monthsLeft}
              onChange={(event) => updateEditCreditField("monthsLeft", event.target.value)}
              placeholder="Осталось месяцев"
              inputMode="numeric"
              aria-label="Осталось месяцев"
            />
          </div>

          <div className={styles.errorStack}>
            {editCreditErrors.bankName ? <p className={styles.fieldError}>{editCreditErrors.bankName}</p> : null}
            {editCreditErrors.amountRub ? <p className={styles.fieldError}>{editCreditErrors.amountRub}</p> : null}
            {editCreditErrors.monthlyPaymentRub ? <p className={styles.fieldError}>{editCreditErrors.monthlyPaymentRub}</p> : null}
            {editCreditErrors.monthsLeft ? <p className={styles.fieldError}>{editCreditErrors.monthsLeft}</p> : null}
          </div>

          <button type="submit" className={styles.calculateButton}>
            Сохранить
          </button>
        </form>
      </BottomSheetModal>

      <BottomSheetModal
        isOpen={isCreditCalculatorOpen}
        onClose={closeCreditCalculator}
        ariaLabel="Рассчитать кредит или займ"
        backdropClassName={styles.creditSheetBackdrop}
        sheetClassName={styles.creditSheet}
        handleClassName={styles.creditSheetHandle}
      >
        <h2 className={styles.sheetTitle}>Рассчитать кредит / займ</h2>

        <form className={styles.creditForm} onSubmit={handleCalculateCredit}>
          <div className={styles.inputGroupCard}>
            <input
              className={styles.inputRow}
              value={creditForm.loanAmount}
              onChange={(event) => updateFormField("loanAmount", event.target.value)}
              placeholder="Сумма кредита"
              inputMode="decimal"
              aria-label="Сумма кредита"
            />
            <input
              className={styles.inputRow}
              value={creditForm.term}
              onChange={(event) => updateFormField("term", event.target.value)}
              placeholder="Срок"
              inputMode="numeric"
              aria-label="Срок"
            />
            <input
              className={styles.inputRow}
              value={creditForm.monthlyPayment}
              onChange={(event) => updateFormField("monthlyPayment", event.target.value)}
              placeholder="Ежемесячный платеж"
              inputMode="decimal"
              aria-label="Ежемесячный платеж"
            />
            <input
              className={styles.inputRow}
              value={creditForm.interestRate}
              onChange={(event) => updateFormField("interestRate", event.target.value)}
              placeholder="Процентная ставка - опционально"
              inputMode="decimal"
              aria-label="Процентная ставка"
            />
          </div>

          <div className={styles.errorStack}>
            {creditErrors.loanAmount ? <p className={styles.fieldError}>{creditErrors.loanAmount}</p> : null}
            {creditErrors.term ? <p className={styles.fieldError}>{creditErrors.term}</p> : null}
            {creditErrors.monthlyPayment ? <p className={styles.fieldError}>{creditErrors.monthlyPayment}</p> : null}
            {creditErrors.interestRate ? <p className={styles.fieldError}>{creditErrors.interestRate}</p> : null}
          </div>

          <label className={styles.selectPillField}>
            <select
              className={`${styles.selectPill} ${creditForm.loanPurpose ? styles.selectPillSelected : ""}`}
              value={creditForm.loanPurpose}
              onChange={(event) => updateFormField("loanPurpose", event.target.value)}
              aria-label="Цель кредита"
            >
              <option value="">Цель кредита</option>
              {creditPurposeOptions.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <ChevronDown className={styles.selectChevron} size={20} strokeWidth={2} />
          </label>
          {creditErrors.loanPurpose ? <p className={styles.fieldError}>{creditErrors.loanPurpose}</p> : null}

          <label className={styles.selectPillField}>
            <select
              className={`${styles.selectPill} ${creditForm.incomeStability ? styles.selectPillSelected : ""}`}
              value={creditForm.incomeStability}
              onChange={(event) => updateFormField("incomeStability", event.target.value)}
              aria-label="Устойчивость дохода"
            >
              <option value="">Устойчивость дохода</option>
              {incomeStabilityOptions.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <ChevronDown className={styles.selectChevron} size={20} strokeWidth={2} />
          </label>
          {creditErrors.incomeStability ? <p className={styles.fieldError}>{creditErrors.incomeStability}</p> : null}

          <button type="submit" className={styles.calculateButton}>
            Рассчитать
          </button>
        </form>
      </BottomSheetModal>

      <BottomSheetModal
        isOpen={isCreditResultOpen}
        onClose={closeCreditResult}
        ariaLabel="Вывод по расчету кредита"
        backdropClassName={styles.creditSheetBackdrop}
        sheetClassName={styles.creditSheet}
        handleClassName={styles.creditSheetHandle}
      >
        <h2 className={`${styles.sheetTitle} ${styles.resultSheetTitle}`}>Вывод по расчету</h2>

        <section className={styles.resultCard}>
          <div className={styles.resultHeader}>
            <span
              className={`${styles.riskDot} ${
                creditResult?.status === "danger" ? styles.riskDanger : creditResult?.status === "safe" ? styles.riskSafe : styles.riskCaution
              }`}
            />
            <h3 className={styles.resultStatus}>{creditResult?.statusText ?? "Осторожно"}</h3>
          </div>

          <div className={styles.resultMetrics}>
            <div className={styles.resultMetricRow}>
              <span>Оценочный платеж</span>
              <strong>{creditResult ? `${formatRub(creditResult.estimatedPayment)} руб` : "—"}</strong>
            </div>
            <div className={styles.resultMetricRow}>
              <span>Ваш платеж</span>
              <strong>{creditResult ? `${formatRub(creditResult.enteredPayment)} руб` : "—"}</strong>
            </div>
            <div className={styles.resultMetricRow}>
              <span>Переплата за срок</span>
              <strong>{creditResult ? `${formatRub(creditResult.totalOverpayment)} руб` : "—"}</strong>
            </div>
          </div>

          <p className={styles.resultRecommendation}>{creditResult?.recommendation ?? ""}</p>

          <button type="button" className={styles.detailsButton} onClick={handleOpenConsultantWithResult}>
            Подробнее
          </button>
        </section>
      </BottomSheetModal>
    </main>
  );
}
