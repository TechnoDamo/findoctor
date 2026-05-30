'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function NewTransferPage() {
  const [fromAccount, setFromAccount] = useState('');
  const [toAccount, setToAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Новый перевод</h1>
        <p className="text-gray-500">Перевод средств между счетами</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Детали перевода</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="from">Со счёта</Label>
                <select id="from" className="w-full p-2 border rounded" value={fromAccount} onChange={(e) => setFromAccount(e.target.value)} required>
                  <option value="">Выберите счёт</option>
                  <option>Основной счёт</option>
                  <option>Накопительный счёт</option>
                  <option>Брокерский счёт</option>
                </select>
              </div>
              <div>
                <Label htmlFor="to">На счёт</Label>
                <select id="to" className="w-full p-2 border rounded" value={toAccount} onChange={(e) => setToAccount(e.target.value)} required>
                  <option value="">Выберите счёт</option>
                  <option>Основной счёт</option>
                  <option>Накопительный счёт</option>
                  <option>Брокерский счёт</option>
                </select>
              </div>
            </div>
            <div>
              <Label htmlFor="amount">Сумма (₽)</Label>
              <Input id="amount" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="date">Дата</Label>
              <Input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="desc">Описание</Label>
              <Input id="desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Например: перевод на накопления" />
            </div>
            <Button type="submit" className="w-full">Выполнить перевод</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
