import { financeMetrics, formatRub } from "@/lib/financeData";

export type FinanceSection = {
  slug: string;
  title: string;
  subtitle: string;
  amount?: string;
};

export const financeSections: FinanceSection[] = [
  { slug: "profile_page", title: "Профиль", subtitle: "Настройки и персональные данные" },
  { slug: "achievements_page", title: "Достижения", subtitle: "Ваши баллы и достижения", amount: "433 балла" },
  { slug: "day_spending_page", title: "Дневной расход", subtitle: "Сумма трат за текущий день", amount: "12 400 руб" },
  { slug: "income_page", title: "Доходы", subtitle: "Доходы за текущий месяц", amount: formatRub(financeMetrics.incomeRub) },
  { slug: "expenses_page", title: "Расходы", subtitle: "Расходы за текущий месяц", amount: formatRub(financeMetrics.expensesRub) },
  { slug: "credit_traffic_page", title: "Кредитный светофор", subtitle: "Индикатор кредитной нагрузки" },
  { slug: "financial_health_page", title: "Финансовое здоровье", subtitle: "Тестовый экран для оценки финансового состояния" },
  { slug: "savings_page", title: "Копилка", subtitle: "Накопления по цели", amount: "50 000 руб" },
  { slug: "cushion_page", title: "Подушка", subtitle: "Финансовая подушка безопасности", amount: formatRub(financeMetrics.cushionRub) },
  { slug: "consultant_page", title: "Мой Консультант", subtitle: "Чат и персональные рекомендации" },
  { slug: "consultant_audio_page", title: "Голосовой Консультант", subtitle: "Голосовой режим общения с консультантом" }
];

export const financeSectionsBySlug = Object.fromEntries(financeSections.map((section) => [section.slug, section])) as Record<string, FinanceSection>;
