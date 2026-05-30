export const numberFormatter = new Intl.NumberFormat("ru-RU");

export function formatRub(value: number) {
  return `${numberFormatter.format(value)} руб`;
}

export type FinanceMetrics = {
  incomeRub: number;
  expensesRub: number;
  balanceRub: number;
  points: number;
  cushionRub: number;
  recommendedCushionRub: number;
  essentialMonthlySpendRub: number;
};

export const financeMetrics: FinanceMetrics = {
  incomeRub: 240000,
  expensesRub: 47000,
  balanceRub: 425000,
  points: 433,
  cushionRub: 100000,
  recommendedCushionRub: 100000,
  essentialMonthlySpendRub: 167000,
};

export function getCushionStats(metrics: FinanceMetrics = financeMetrics) {
  const dailyBurnRub = metrics.essentialMonthlySpendRub / 30;
  const daysCovered = dailyBurnRub > 0 ? Math.max(Math.round(metrics.cushionRub / dailyBurnRub), 0) : 0;
  const autoTopUpRub = Math.max(metrics.recommendedCushionRub - metrics.cushionRub, 0);

  return {
    daysCovered,
    autoTopUpRub,
  };
}
