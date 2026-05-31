'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateGoal } from '@/lib/api/queries/goals';
import { apiErrorMessage } from '@/lib/api/errors';

export default function NewGoalPage() {
  const router = useRouter();
  const createGoal = useCreateGoal();
  const [name, setName] = useState('');
  const [target, setTarget] = useState('');
  const [current, setCurrent] = useState('');
  const [deadline, setDeadline] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!name) { setError('Введите название'); return; }
    if (!target || isNaN(parseFloat(target))) { setError('Введите целевую сумму'); return; }

    try {
      await createGoal.mutateAsync({
        name,
        target_amount: parseFloat(target).toFixed(2),
        current_amount: current ? parseFloat(current).toFixed(2) : '0',
        deadline: deadline || null,
      });
      router.push('/dashboard/goals');
    } catch (err) {
      setError(apiErrorMessage(err, 'Не удалось создать цель'));
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Добавить цель</h1>
        <p className="text-gray-500">Поставьте финансовую цель</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Информация о цели</CardTitle></CardHeader>
        <CardContent>
          {error && <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Название</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Например: Подушка безопасности" required />
            </div>
            <div>
              <Label htmlFor="target">Целевая сумма</Label>
              <Input id="target" type="number" step="0.01" min="0.01" value={target} onChange={(e) => setTarget(e.target.value)} placeholder="Сколько хотите накопить" required />
            </div>
            <div>
              <Label htmlFor="current">Текущая сумма</Label>
              <Input id="current" type="number" step="0.01" min="0" value={current} onChange={(e) => setCurrent(e.target.value)} placeholder="Сколько уже накоплено" />
            </div>
            <div>
              <Label htmlFor="deadline">Дедлайн</Label>
              <Input id="deadline" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={createGoal.isLoading}>
                {createGoal.isLoading ? 'Создаём...' : 'Создать'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Отмена</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
