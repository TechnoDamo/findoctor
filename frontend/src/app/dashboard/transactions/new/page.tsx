'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateTransaction } from '@/lib/api/queries/transactions';
import { useAccounts } from '@/lib/api/queries/accounts';
import { apiErrorMessage } from '@/lib/api/errors';

export default function NewTransactionPage() {
  const router = useRouter();
  const { data: accounts } = useAccounts();
  const createTx = useCreateTransaction();

  const [type, setType] = useState<'income' | 'expense'>('expense');
  const [accountId, setAccountId] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(new Date().toISOString().slice(0, 16));
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!accountId) { setError('Выберите счёт'); return; }
    if (!amount || isNaN(parseFloat(amount))) { setError('Введите сумму'); return; }

    try {
      await createTx.mutateAsync({
        account_id: accountId,
        type,
        amount: parseFloat(amount).toFixed(2),
        currency: 'RUB',
        transaction_datetime: new Date(date).toISOString(),
        description: description || null,
      });
      router.push('/dashboard/transactions');
    } catch (err) {
      setError(apiErrorMessage(err, 'Не удалось создать транзакцию'));
    }
  };

  const accountsList = accounts || [];

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Добавить транзакцию</h1>
        <p className="text-gray-500">Доход или расход</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Детали транзакции</CardTitle></CardHeader>
        <CardContent>
          {error && <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="type">Тип</Label>
              <select id="type" className="w-full p-2 border rounded" value={type} onChange={(e) => setType(e.target.value as 'income' | 'expense')}>
                <option value="expense">Расход</option>
                <option value="income">Доход</option>
              </select>
            </div>
            <div>
              <Label htmlFor="account">Счёт</Label>
              <select id="account" className="w-full p-2 border rounded" value={accountId} onChange={(e) => setAccountId(e.target.value)}>
                <option value="">Выберите счёт</option>
                {accountsList.map((a) => (
                  <option key={a.id} value={a.id}>{a.name} ({a.currency})</option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="amount">Сумма</Label>
              <Input id="amount" type="number" step="0.01" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="1000.00" required />
            </div>
            <div>
              <Label htmlFor="date">Дата</Label>
              <Input id="date" type="datetime-local" value={date} onChange={(e) => setDate(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="description">Описание</Label>
              <Input id="description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Например: Продукты" />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={createTx.isLoading}>
                {createTx.isLoading ? 'Создаём...' : 'Создать'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Отмена</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
