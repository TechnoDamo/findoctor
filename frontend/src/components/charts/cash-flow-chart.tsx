'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const data = [
  { month: 'Янв', income: 400000, expenses: 240000 },
  { month: 'Фев', income: 350000, expenses: 280000 },
  { month: 'Мар', income: 420000, expenses: 310000 },
  { month: 'Апр', income: 380000, expenses: 290000 },
  { month: 'Май', income: 410000, expenses: 320000 },
  { month: 'Июн', income: 390000, expenses: 305000 },
  { month: 'Июл', income: 430000, expenses: 330000 },
];

function formatRUB(value: number) {
  return `${(value / 1000).toFixed(1)} тыс`;
}

export function CashFlowChart() {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
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
