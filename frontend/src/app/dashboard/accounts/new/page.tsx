'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateAccount } from '@/lib/api/queries/accounts';
import { apiErrorMessage } from '@/lib/api/errors';

export default function NewAccountPage() {
  const router = useRouter();
  const createAccount = useCreateAccount();
  const [name, setName] = useState('');
  const [institutionName, setInstitutionName] = useState('');
  const [typeId, setTypeId] = useState('');
  const [openingBalance, setOpeningBalance] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!name) { setError('Введите название'); return; }

    try {
      await createAccount.mutateAsync({
        name,
        account_type_id: typeId || null,
        institution_name: institutionName || null,
        currency: 'RUB',
        opening_balance: openingBalance ? parseFloat(openingBalance).toFixed(2) : '0',
      });
      router.push('/dashboard/accounts');
    } catch (err) {
      setError(apiErrorMessage(err, 'Не удалось создать счёт'));
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Новый счёт</h1>
        <p className="text-gray-500">Добавьте банковский счёт</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Информация о счёте</CardTitle></CardHeader>
        <CardContent>
          {error && <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Название</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Например: Основной счёт" required />
            </div>
            <div>
              <Label htmlFor="type">Тип счета (ID)</Label>
              <Input id="type" value={typeId} onChange={(e) => setTypeId(e.target.value)} placeholder="UUID типа счета" />
            </div>
            <div>
              <Label htmlFor="institution">Банк / учреждение</Label>
              <Input id="institution" value={institutionName} onChange={(e) => setInstitutionName(e.target.value)} placeholder="Например: Сбербанк" />
            </div>
            <div>
              <Label htmlFor="balance">Начальный баланс</Label>
              <Input id="balance" type="number" step="0.01" min="0" value={openingBalance} onChange={(e) => setOpeningBalance(e.target.value)} placeholder="0" />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={createAccount.isLoading}>
                {createAccount.isLoading ? 'Создаём...' : 'Создать'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Отмена</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
