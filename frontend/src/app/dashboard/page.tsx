'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useDashboardSummary } from '@/lib/api/queries/analytics';
import { useTransactions } from '@/lib/api/queries/transactions';

function formatRub(value: number | string) {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(n)) return '0 ₽';
  return `${Math.abs(n).toLocaleString('ru-RU')} ₽`;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

export default function DashboardPage() {
  const router = useRouter();
  const summary = useDashboardSummary();
  const recentTx = useTransactions({ page: 1, page_size: 5 });

  const isLoading = summary.isLoading;
  const isError = summary.isError;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-32" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 w-full" />
          <Skeleton className="h-80 w-full" />
        </div>
      </div>
    );
  }

  if (isError || !summary.data) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Обзор</h1>
        <Card><CardContent className="p-6 text-center text-red-500">Не удалось загрузить данные</CardContent></Card>
      </div>
    );
  }

  const s = summary.data;
  const totalCash = parseFloat(s.total_cash) || 0;
  const totalAssets = parseFloat(s.total_assets) || 0;
  const totalLiabilities = Math.abs(parseFloat(s.total_liabilities) || 0);
  const netWorth = parseFloat(s.net_worth) || 0;
  const monthlyIncome = parseFloat(s.monthly_income) || 0;
  const monthlyExpenses = Math.abs(parseFloat(s.monthly_expenses) || 0);
  const savingsRate = s.savings_rate != null ? s.savings_rate : (monthlyIncome > 0 ? ((monthlyIncome - monthlyExpenses) / monthlyIncome * 100) : 0);
  const transactions = recentTx.data?.items || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <h1 className="text-3xl font-bold">Обзор</h1>
        <Button onClick={() => router.push('/dashboard/transactions/new')}>Добавить транзакцию</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Наличные</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 18V6"/></svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCash >= 0 ? '' : '−'}{formatRub(totalCash)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Активы</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAssets >= 0 ? '' : '−'}{formatRub(totalAssets)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Обязательства</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">−{formatRub(totalLiabilities)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Капитал</CardTitle>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${netWorth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {netWorth >= 0 ? '' : '−'}{formatRub(netWorth)}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Последние транзакции</CardTitle>
            <CardDescription>5 последних операций</CardDescription>
          </CardHeader>
          <CardContent>
            {transactions.length === 0 ? (
              <div className="text-center text-gray-500 py-4">Пока нет транзакций</div>
            ) : (
              <div className="space-y-3">
                {transactions.map((tx) => (
                  <div key={tx.id} className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{tx.description || tx.merchant_name || tx.type}</p>
                      <p className="text-sm text-muted-foreground">{formatDate(tx.transaction_datetime)}</p>
                    </div>
                    <div className={`font-bold ${tx.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                      {tx.type === 'income' ? '+' : '−'}{formatRub(tx.amount)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
          <CardFooter>
            <Button variant="outline" onClick={() => router.push('/dashboard/transactions')}>Все транзакции</Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Сводка за месяц</CardTitle>
            <CardDescription>Доходы, расходы и норма сбережений</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span>Доходы</span>
                <span className="font-bold text-green-600">{formatRub(monthlyIncome)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Расходы</span>
                <span className="font-bold text-red-600">−{formatRub(monthlyExpenses)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Сбережения</span>
                <span className="font-bold text-blue-600">{monthlyIncome - monthlyExpenses >= 0 ? '+' : '−'}{formatRub(Math.abs(monthlyIncome - monthlyExpenses))}</span>
              </div>
              <div className="border-t pt-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Норма сбережений</span>
                  <span className="font-bold">{Math.round(savingsRate)}%</span>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button variant="outline" onClick={() => router.push('/dashboard/analytics')}>Подробнее</Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
