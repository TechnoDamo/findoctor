'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function NewLiabilityPage() {
  const [name, setName] = useState('');
  const [type, setType] = useState('');
  const [bank, setBank] = useState('');
  const [balance, setBalance] = useState('');
  const [payment, setPayment] = useState('');
  const [rate, setRate] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Добавить обязательство</h1>
        <p className="text-gray-500">Кредит, ипотека или долг</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Информация об обязательстве</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Название</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Например: Ипотека, Автокредит" required />
            </div>
            <div>
              <Label htmlFor="type">Тип</Label>
              <select id="type" className="w-full p-2 border rounded" value={type} onChange={(e) => setType(e.target.value)} required>
                <option value="">Выберите тип</option>
                <option>Ипотека</option>
                <option>Автокредит</option>
                <option>Потребкредит</option>
                <option>Кредитная карта</option>
                <option>Долг</option>
              </select>
            </div>
            <div>
              <Label htmlFor="bank">Банк / кредитор</Label>
              <Input id="bank" value={bank} onChange={(e) => setBank(e.target.value)} placeholder="Сбербанк, ВТБ..." />
            </div>
            <div>
              <Label htmlFor="balance">Текущий остаток (₽)</Label>
              <Input id="balance" type="number" value={balance} onChange={(e) => setBalance(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="payment">Ежемесячный платёж (₽)</Label>
              <Input id="payment" type="number" value={payment} onChange={(e) => setPayment(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="rate">Процентная ставка (%)</Label>
              <Input id="rate" type="number" value={rate} onChange={(e) => setRate(e.target.value)} />
            </div>
            <Button type="submit" className="w-full">Добавить обязательство</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
