'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';
import type { CashFlowSeries } from '@/lib/api/types';

function formatRUB(value: number) {
  return `${(value / 1000).toFixed(1)} тыс`;
}

function formatLabel(dateStr: string) {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { month: 'short', year: '2-digit' });
  } catch {
    return dateStr;
  }
}

interface Props {
  data?: CashFlowSeries;
  isLoading?: boolean;
  isError?: boolean;
}

export function CashFlowChart({ data, isLoading, isError }: Props) {
  if (isLoading) {
    return <Skeleton className="h-80 w-full" />;
  }

  if (isError || !data?.items?.length) {
    return (
      <div className="h-80 flex items-center justify-center text-sm text-gray-500">
        {isError ? 'Не удалось загрузить данные' : 'Нет данных о денежном потоке'}
      </div>
    );
  }

  const chartData = data.items.map((point) => ({
    period: formatLabel(point.period_start),
    income: parseFloat(point.income) || 0,
    expenses: Math.abs(parseFloat(point.expenses) || 0),
  }));

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis tickFormatter={formatRUB} />
          <Tooltip
            formatter={(value) => [`₽${Number(value).toLocaleString('ru-RU')}`, '']}
          />
          <Legend formatter={(value: string) => value === 'income' ? 'Доходы' : 'Расходы'} />
          <Bar dataKey="income" fill="#10b981" name="income" />
          <Bar dataKey="expenses" fill="#ef4444" name="expenses" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
