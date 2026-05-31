'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateLiability } from '@/lib/api/queries/liabilities';
import { apiErrorMessage } from '@/lib/api/errors';

export default function NewLiabilityPage() {
  const router = useRouter();
  const createLiability = useCreateLiability();
  const [name, setName] = useState('');
  const [typeId, setTypeId] = useState('');
  const [creditorName, setCreditorName] = useState('');
  const [balance, setBalance] = useState('');
  const [payment, setPayment] = useState('');
  const [rate, setRate] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!name) { setError('Введите название'); return; }
    if (!balance || isNaN(parseFloat(balance))) { setError('Введите баланс'); return; }

    try {
      await createLiability.mutateAsync({
        name,
        liability_type_id: typeId || null,
        creditor_name: creditorName || null,
        current_balance: parseFloat(balance).toFixed(2),
        currency: 'RUB',
        regular_payment_amount: payment ? parseFloat(payment).toFixed(2) : null,
        interest_rate: rate ? parseFloat(rate) : null,
      });
      router.push('/dashboard/liabilities');
    } catch (err) {
      setError(apiErrorMessage(err, 'Не удалось создать'));
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Добавить обязательство</h1>
        <p className="text-gray-500">Кредит, ипотека или долг</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Информация об обязательстве</CardTitle></CardHeader>
        <CardContent>
          {error && <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Название</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Например: Ипотека" required />
            </div>
            <div>
              <Label htmlFor="type">Тип (ID)</Label>
              <Input id="type" value={typeId} onChange={(e) => setTypeId(e.target.value)} placeholder="UUID типа" />
            </div>
            <div>
              <Label htmlFor="creditor">Кредитор</Label>
              <Input id="creditor" value={creditorName} onChange={(e) => setCreditorName(e.target.value)} placeholder="Например: Сбербанк" />
            </div>
            <div>
              <Label htmlFor="balance">Текущий баланс</Label>
              <Input id="balance" type="number" step="0.01" min="0.01" value={balance} onChange={(e) => setBalance(e.target.value)} placeholder="Сумма долга" required />
            </div>
            <div>
              <Label htmlFor="payment">Ежемесячный платёж</Label>
              <Input id="payment" type="number" step="0.01" min="0" value={payment} onChange={(e) => setPayment(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="rate">Процентная ставка (%)</Label>
              <Input id="rate" type="number" step="0.01" min="0" value={rate} onChange={(e) => setRate(e.target.value)} />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={createLiability.isLoading}>
                {createLiability.isLoading ? 'Создаём...' : 'Создать'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Отмена</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
