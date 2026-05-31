'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useTransfers } from '@/lib/api/queries/transfers';

function formatRub(value: number) {
  return `${value.toLocaleString('ru-RU')} ₽`;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

export default function TransfersPage() {
  const router = useRouter();
  const { data, isLoading, isError } = useTransfers();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-40" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Переводы</h1>
        <Card><CardContent className="p-6 text-center text-red-500">Не удалось загрузить переводы</CardContent></Card>
      </div>
    );
  }

  const transfers = data?.items || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Переводы</h1>
          <p className="text-gray-500">Переводы между счетами</p>
        </div>
        <Button onClick={() => router.push('/dashboard/transfers/new')}>Новый перевод</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>История переводов</CardTitle>
          <CardDescription>Последние операции</CardDescription>
        </CardHeader>
        <CardContent>
          {transfers.length === 0 ? (
            <div className="text-center text-gray-500 py-8">Пока нет переводов</div>
          ) : (
            <div className="space-y-2">
              {transfers.map((tr) => (
                <div key={tr.id} className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                  <div>
                    <p className="font-medium">
                      {tr.from_transaction?.account_id || tr.from_account_id} → {tr.to_transaction?.account_id || tr.to_account_id}
                    </p>
                    <p className="text-sm text-muted-foreground">{formatDate(tr.transaction_datetime)}</p>
                    {tr.description && <p className="text-sm text-muted-foreground">{tr.description}</p>}
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{formatRub(tr.amount)}</p>
                    <p className="text-sm text-muted-foreground">{tr.currency}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
