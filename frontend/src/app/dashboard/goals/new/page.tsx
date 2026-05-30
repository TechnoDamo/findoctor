'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function NewGoalPage() {
  const [name, setName] = useState('');
  const [target, setTarget] = useState('');
  const [current, setCurrent] = useState('');
  const [deadline, setDeadline] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Добавить цель</h1>
        <p className="text-gray-500">Поставьте финансовую цель</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Информация о цели</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Название</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Подушка безопасности, На квартиру..." required />
            </div>
            <div>
              <Label htmlFor="target">Целевая сумма (₽)</Label>
              <Input id="target" type="number" value={target} onChange={(e) => setTarget(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="current">Текущая сумма (₽)</Label>
              <Input id="current" type="number" value={current} onChange={(e) => setCurrent(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="deadline">Срок</Label>
              <Input id="deadline" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
            </div>
            <Button type="submit" className="w-full">Добавить цель</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
