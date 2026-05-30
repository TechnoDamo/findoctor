'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function NewAssetPage() {
  const [name, setName] = useState('');
  const [type, setType] = useState('');
  const [value, setValue] = useState('');
  const [date, setDate] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Добавить актив</h1>
        <p className="text-gray-500">Недвижимость, транспорт, инвестиции</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Информация об активе</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Название</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Например: Квартира, Автомобиль" required />
            </div>
            <div>
              <Label htmlFor="type">Тип актива</Label>
              <select id="type" className="w-full p-2 border rounded" value={type} onChange={(e) => setType(e.target.value)} required>
                <option value="">Выберите тип</option>
                <option>Недвижимость</option>
                <option>Транспорт</option>
                <option>Ценные бумаги</option>
                <option>Драгоценности</option>
                <option>Другое</option>
              </select>
            </div>
            <div>
              <Label htmlFor="value">Оценочная стоимость (₽)</Label>
              <Input id="value" type="number" value={value} onChange={(e) => setValue(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="date">Дата покупки</Label>
              <Input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
            <Button type="submit" className="w-full">Добавить актив</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
