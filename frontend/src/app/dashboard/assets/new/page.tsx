'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateAsset } from '@/lib/api/queries/assets';
import { apiErrorMessage } from '@/lib/api/errors';

export default function NewAssetPage() {
  const router = useRouter();
  const createAsset = useCreateAsset();
  const [name, setName] = useState('');
  const [typeId, setTypeId] = useState('');
  const [value, setValue] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [date, setDate] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!name) { setError('Введите название'); return; }
    if (!value || isNaN(parseFloat(value))) { setError('Введите стоимость'); return; }

    try {
      await createAsset.mutateAsync({
        name,
        asset_type_id: typeId || null,
        estimated_value: parseFloat(value).toFixed(2),
        currency: 'RUB',
        purchase_price: purchasePrice ? parseFloat(purchasePrice).toFixed(2) : null,
        purchase_date: date || null,
      });
      router.push('/dashboard/assets');
    } catch (err) {
      setError(apiErrorMessage(err, 'Не удалось создать актив'));
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Добавить актив</h1>
        <p className="text-gray-500">Недвижимость, транспорт, инвестиции</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Информация об активе</CardTitle></CardHeader>
        <CardContent>
          {error && <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Название</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Например: Квартира" required />
            </div>
            <div>
              <Label htmlFor="type">Тип актива (ID)</Label>
              <Input id="type" value={typeId} onChange={(e) => setTypeId(e.target.value)} placeholder="UUID типа актива" />
            </div>
            <div>
              <Label htmlFor="value">Стоимость</Label>
              <Input id="value" type="number" step="0.01" min="0.01" value={value} onChange={(e) => setValue(e.target.value)} placeholder="Текущая рыночная стоимость" required />
            </div>
            <div>
              <Label htmlFor="purchasePrice">Цена покупки</Label>
              <Input id="purchasePrice" type="number" step="0.01" min="0" value={purchasePrice} onChange={(e) => setPurchasePrice(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="date">Дата покупки</Label>
              <Input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={createAsset.isLoading}>
                {createAsset.isLoading ? 'Создаём...' : 'Создать'}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>Отмена</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
