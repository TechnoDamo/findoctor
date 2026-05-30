'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { date: 'Янв 24', netWorth: 950000 },
  { date: 'Фев 24', netWorth: 980000 },
  { date: 'Мар 24', netWorth: 1020000 },
  { date: 'Апр 24', netWorth: 1080000 },
  { date: 'Май 24', netWorth: 1120000 },
  { date: 'Июн 24', netWorth: 1180000 },
  { date: 'Июл 24', netWorth: 1150000 },
  { date: 'Авг 24', netWorth: 1210000 },
  { date: 'Сен 24', netWorth: 1240000 },
  { date: 'Окт 24', netWorth: 1280000 },
  { date: 'Ноя 24', netWorth: 1300000 },
  { date: 'Дек 24', netWorth: 1310000 },
];

function formatRUB(value: number) {
  return `${(value / 1000).toFixed(0)} тыс`;
}

export function NetWorthChart() {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
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
