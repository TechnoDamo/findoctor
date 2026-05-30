'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function NewTransactionPage() {
  const [type, setType] = useState<'income' | 'expense' | 'transfer'>('expense');
  const [account, setAccount] = useState('');
  const [category, setCategory] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(new Date().toISOString());
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Добавить транзакцию</h1>
        <p className="text-gray-500">Доход, расход или перевод</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Детали транзакции</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Тип</Label>
              <div className="flex gap-2 mt-1">
                {[
                  { value: 'income', label: 'Доход', color: 'bg-green-100 text-green-700 border-green-300' },
                  { value: 'expense', label: 'Расход', color: 'bg-red-100 text-red-700 border-red-300' },
                  { value: 'transfer', label: 'Перевод', color: 'bg-blue-100 text-blue-700 border-blue-300' },
                ].map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setType(t.value as typeof type)}
                    className={`px-4 py-2 rounded-md border font-medium transition-colors ${type === t.value ? t.color + ' border-2' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Label htmlFor="account">Счёт</Label>
              <select id="account" className="w-full p-2 border rounded" value={account} onChange={(e) => setAccount(e.target.value)} required>
                <option value="">Выберите счёт</option>
                <option>Основной счёт</option>
                <option>Накопительный счёт</option>
                <option>Кредитная карта</option>
                <option>Брокерский счёт</option>
              </select>
            </div>
            <div>
              <Label htmlFor="category">Категория</Label>
              <select id="category" className="w-full p-2 border rounded" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">Выберите категорию</option>
                {type === 'income' ? (
                  <>
                    <option>Зарплата</option>
                    <option>Фриланс</option>
                    <option>Инвестиции</option>
                    <option>Подарок</option>
                  </>
                ) : type === 'expense' ? (
                  <>
                    <option>Продукты</option>
                    <option>Транспорт</option>
                    <option>Жильё</option>
                    <option>Развлечения</option>
                    <option>Здоровье</option>
                  </>
                ) : (
                  <>
                    <option>Перевод на счёт</option>
                    <option>Инвестирование</option>
                    <option>Погашение долга</option>
                  </>
                )}
              </select>
            </div>
            <div>
              <Label htmlFor="amount">Сумма (₽)</Label>
              <Input id="amount" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="date">Дата и время</Label>
              <Input id="date" type="datetime-local" value={date} onChange={(e) => setDate(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="desc">Описание</Label>
              <Input id="desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Например: продукты в Пятёрочке" />
            </div>
            <Button type="submit" className="w-full">Добавить транзакцию</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
