'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateTransfer } from '@/lib/api/queries/transfers';
import { useAccounts } from '@/lib/api/queries/accounts';
import { apiErrorMessage } from '@/lib/api/errors';

export default function NewTransferPage() {
  const router = useRouter();
  const { data: accounts } = useAccounts();
  const createTransfer = useCreateTransfer();
  const [fromAccount, setFromAccount] = useState('');
  const [toAccount, setToAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!fromAccount || !toAccount) { setError('Выберите счета'); return; }
    if (fromAccount === toAccount) { setError('Счета должны быть разными'); return; }
    if (!amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) { setError('Введите положительную сумму'); return; }

    try {
      await createTransfer.mutateAsync({
        from_account_id: fromAccount,
        to_account_id: toAccount,
        amount: parseFloat(amount).toFixed(2),
        currency: 'RUB',
        transaction_datetime: new Date(date).toISOString(),
        description: description || null,
      });
      router.push('/dashboard/transfers');
    } catch (err) {
      setError(apiErrorMessage(err, 'Не удалось создать перевод'));
    }
  };

  const accountsList = accounts || [];

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Новый перевод</h1>
        <p className="text-gray-500">Перевод средств между счетами</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Детали перевода</CardTitle>
          <CardDescription>Переведите деньги между вашими счетами</CardDescription>
        </CardHeader>
        <CardContent>
          {error && <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="from">Со счета</Label>
              <select id="from" className="w-full p-2 border rounded" value={fromAccount} onChange={(e) => setFromAccount(e.target.value)}>
                <option value="">Выберите счёт</option>
                {accountsList.map((a) => (
                  <option key={a.id} value={a.id} disabled={a.id === toAccount}>{a.name} ({a.currency})</option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="to">На счет</Label>
              <select id="to" className="w-full p-2 border rounded" value={toAccount} onChange={(e) => setToAccount(e.target.value)}>
                <option value="">Выберите счёт</option>
                {accountsList.map((a) => (
                  <option key={a.id} value={a.id} disabled={a.id === fromAccount}>{a.name} ({a.currency})</option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="amount">Сумма</Label>
              <Input id="amount" type="number" step="0.01" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="1000.00" required />
            </div>
            <div>
              <Label htmlFor="date">Дата</Label>
              <Input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="description">Описание</Label>
              <Input id="description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Назначение перевода" />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={createTransfer.isLoading}>
                {createTransfer.isLoading ? 'Отправляем...' : 'Перевести'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Отмена</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
