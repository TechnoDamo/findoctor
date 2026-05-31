'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useAccounts } from '@/lib/api/queries/accounts';

function formatRub(value: number) {
  return `${value.toLocaleString('ru-RU')} ₽`;
}

export default function AccountsPage() {
  const router = useRouter();
  const { data: accounts, isLoading, isError } = useAccounts();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-10 w-40" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-36" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Счета</h1>
        <Card>
          <CardContent className="p-6 text-center text-red-500">
            Не удалось загрузить счета
          </CardContent>
        </Card>
      </div>
    );
  }

  const accountsList = accounts || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Счета</h1>
          <p className="text-gray-500">Управление банковскими счетами</p>
        </div>
        <Button onClick={() => router.push('/dashboard/accounts/new')}>Добавить счёт</Button>
      </div>

      {accountsList.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-gray-500">
            Пока нет счетов. Добавьте первый счёт.
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {accountsList.slice(0, 3).map((account) => (
              <Card key={account.id}>
                <CardHeader>
                  <CardTitle>{account.name}</CardTitle>
                  <CardDescription>{account.institution_name || account.currency}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${account.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {account.balance >= 0 ? '' : '−'}{formatRub(Math.abs(account.balance))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Все счета</CardTitle>
              <CardDescription>{accountsList.length} активных счетов</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {accountsList.map((account) => (
                  <div
                    key={account.id}
                    className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                  >
                    <div>
                      <p className="font-medium">{account.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {account.is_active ? 'Активен' : 'Архивирован'} • {account.currency}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${account.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {account.balance >= 0 ? '' : '−'}{formatRub(Math.abs(account.balance))}
                      </p>
                      {account.institution_name && (
                        <p className="text-sm text-muted-foreground">{account.institution_name}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
