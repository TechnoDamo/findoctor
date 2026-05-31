'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';
import type { NetWorthSeries } from '@/lib/api/types';

function formatRUB(value: number) {
  return `${(value / 1000).toFixed(0)} тыс`;
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
  data?: NetWorthSeries;
  isLoading?: boolean;
  isError?: boolean;
}

export function NetWorthChart({ data, isLoading, isError }: Props) {
  if (isLoading) {
    return <Skeleton className="h-80 w-full" />;
  }

  if (isError || !data?.items?.length) {
    return (
      <div className="h-80 flex items-center justify-center text-sm text-gray-500">
        {isError ? 'Не удалось загрузить данные' : 'Нет данных о капитале'}
      </div>
    );
  }

  const chartData = data.items.map((point) => ({
    date: formatLabel(point.date),
    netWorth: parseFloat(point.net_worth) || 0,
  }));

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis tickFormatter={formatRUB} />
          <Tooltip formatter={(value) => [`₽${Number(value).toLocaleString('ru-RU')}`, 'Капитал']} />
          <Area type="monotone" dataKey="netWorth" stroke="#3b82f6" fill="#93c5fd" name="Капитал" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
