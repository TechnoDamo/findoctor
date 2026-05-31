'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useAssets } from '@/lib/api/queries/assets';

function formatRub(value: number) {
  return `${value.toLocaleString('ru-RU')} ₽`;
}

export default function AssetsPage() {
  const router = useRouter();
  const { data: assets, isLoading, isError } = useAssets();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-40" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2].map((i) => <Skeleton key={i} className="h-40 w-full" />)}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Активы</h1>
        <Card><CardContent className="p-6 text-center text-red-500">Не удалось загрузить активы</CardContent></Card>
      </div>
    );
  }

  const assetsList = assets || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Активы</h1>
          <p className="text-gray-500">Имущество, инвестиции и ценности</p>
        </div>
        <Button onClick={() => router.push('/dashboard/assets/new')}>Добавить актив</Button>
      </div>

      {assetsList.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-gray-500">Пока нет активов. Добавьте первый.</CardContent></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assetsList.map((asset) => (
            <Card key={asset.id}>
              <CardHeader>
                <CardTitle>{asset.name}</CardTitle>
                <CardDescription>{asset.currency}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{formatRub(asset.estimated_value)}</div>
                {asset.purchase_date && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Куплен: {new Date(asset.purchase_date).toLocaleDateString('ru-RU')}
                  </p>
                )}
                {asset.purchase_price != null && (
                  <p className="text-sm text-muted-foreground">
                    Цена покупки: {formatRub(asset.purchase_price)}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
