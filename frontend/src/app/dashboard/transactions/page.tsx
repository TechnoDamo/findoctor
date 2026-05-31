'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { useTransactions } from '@/lib/api/queries/transactions';

function formatRub(value: number) {
  return `${value.toLocaleString('ru-RU')} ₽`;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

const typeLabels: Record<string, string> = {
  income: 'Доход',
  expense: 'Расход',
  transfer: 'Перевод',
};

export default function TransactionsPage() {
  const router = useRouter();
  const [typeFilter, setTypeFilter] = useState('');
  const [page, setPage] = useState(1);

  const params: Record<string, unknown> = { page, page_size: 50 };
  if (typeFilter) params.type = typeFilter;

  const { data, isLoading, isError } = useTransactions(params);
  const transactions = data?.items || [];
  const meta = data?.meta;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-48" />
        </div>
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Транзакции</h1>
        <Card>
          <CardContent className="p-6 text-center text-red-500">
            Не удалось загрузить транзакции
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Транзакции</h1>
          <p className="text-gray-500">Просмотр и управление транзакциями</p>
        </div>
        <Button onClick={() => router.push('/dashboard/transactions/new')}>Добавить транзакцию</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Последние транзакции</CardTitle>
            <CardDescription>
              {meta ? `${meta.total_items} операций` : ''}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {transactions.length === 0 ? (
              <div className="text-center text-gray-500 py-8">Пока нет транзакций</div>
            ) : (
              <div className="space-y-2">
                {transactions.map((tx) => (
                  <div
                    key={tx.id}
                    className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                  >
                    <div>
                      <p className="font-medium">{tx.description || tx.merchant_name || tx.type}</p>
                      <p className="text-sm text-muted-foreground">{formatDate(tx.transaction_datetime)}</p>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${tx.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                        {tx.type === 'income' ? '+' : '−'}{formatRub(tx.amount)}
                      </p>
                      <Badge variant="outline">{typeLabels[tx.type] || tx.type}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
          {meta && meta.total_pages > 1 && (
            <CardFooter className="flex justify-between">
              <Button
                variant="outline"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                ← Назад
              </Button>
              <span className="text-sm text-muted-foreground">
                {meta.page} / {meta.total_pages}
              </span>
              <Button
                variant="outline"
                disabled={page >= meta.total_pages}
                onClick={() => setPage(page + 1)}
              >
                Вперёд →
              </Button>
            </CardFooter>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Фильтры</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="type">Тип</Label>
              <select
                id="type"
                className="w-full p-2 border rounded"
                value={typeFilter}
                onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
              >
                <option value="">Все типы</option>
                <option value="income">Доход</option>
                <option value="expense">Расход</option>
                <option value="transfer">Перевод</option>
              </select>
            </div>
            <Button className="w-full" onClick={() => { setTypeFilter(''); setPage(1); }}>
              Сбросить фильтры
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
