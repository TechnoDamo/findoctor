export function formatMoney(amount: string, currency: string = 'RUB'): string {
  if (!amount) return '0';

  const numericAmount = parseFloat(amount);
  if (isNaN(numericAmount)) return '0';

  return numericAmount.toLocaleString('ru-RU', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

export function parseMoney(value: string): number {
  if (!value) return 0;
  const cleaned = value.replace(/[^\d.,\-]/g, '').replace(',', '.');
  return parseFloat(cleaned) || 0;
}

export function getMoneyColor(amount: string): string {
  const numericAmount = parseFloat(amount);
  if (numericAmount > 0) return 'text-green-600';
  if (numericAmount < 0) return 'text-red-600';
  return '';
}
