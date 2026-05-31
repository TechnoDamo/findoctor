'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useLiabilities } from '@/lib/api/queries/liabilities';

function formatRub(value: number) {
  return `${value.toLocaleString('ru-RU')} ₽`;
}

const statusLabels: Record<string, string> = {
  active: 'Активен',
  paid_off: 'Погашен',
  defaulted: 'Просрочен',
  refinanced: 'Рефинансирован',
  closed: 'Закрыт',
};

export default function LiabilitiesPage() {
  const router = useRouter();
  const { data: liabilities, isLoading, isError } = useLiabilities();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <Skeleton className="h-10 w-56" />
          <Skeleton className="h-10 w-52" />
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
        <h1 className="text-3xl font-bold">Обязательства</h1>
        <Card><CardContent className="p-6 text-center text-red-500">Не удалось загрузить обязательства</CardContent></Card>
      </div>
    );
  }

  const list = liabilities || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Обязательства</h1>
          <p className="text-gray-500">Кредиты, ипотека, долги</p>
        </div>
        <Button onClick={() => router.push('/dashboard/liabilities/new')}>Добавить обязательство</Button>
      </div>

      {list.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-gray-500">Пока нет обязательств. Добавьте первое.</CardContent></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {list.map((liab) => (
            <Card key={liab.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{liab.name}</CardTitle>
                    <CardDescription>{liab.creditor_name || liab.currency}</CardDescription>
                  </div>
                  <Badge variant={liab.status === 'active' ? 'default' : 'secondary'}>
                    {statusLabels[liab.status] || liab.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">−{formatRub(liab.current_balance)}</div>
                {liab.regular_payment_amount != null && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Платёж: {formatRub(liab.regular_payment_amount)}/мес
                  </p>
                )}
                {liab.interest_rate != null && (
                  <p className="text-sm text-muted-foreground">
                    Ставка: {liab.interest_rate}%
                  </p>
                )}
                {liab.maturity_date && (
                  <p className="text-sm text-muted-foreground">
                    До: {new Date(liab.maturity_date).toLocaleDateString('ru-RU')}
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
