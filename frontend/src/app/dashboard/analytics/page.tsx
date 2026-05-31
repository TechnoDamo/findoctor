'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { CashFlowChart } from '@/components/charts/cash-flow-chart';
import { NetWorthChart } from '@/components/charts/net-worth-chart';
import { useDashboardSummary, useCashFlow, useNetWorth } from '@/lib/api/queries/analytics';

function formatRub(value: number | string) {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(n)) return '0 ₽';
  return `${Math.abs(n).toLocaleString('ru-RU')} ₽`;
}

export default function AnalyticsPage() {
  const summary = useDashboardSummary();
  const cashFlow = useCashFlow({ groupBy: 'month' });
  const netWorth = useNetWorth();

  const isLoading = summary.isLoading;
  const isError = summary.isError;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (isError || !summary.data) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Аналитика</h1>
        <Card><CardContent className="p-6 text-center text-red-500">Не удалось загрузить данные</CardContent></Card>
      </div>
    );
  }

  const s = summary.data;
  const totalCash = parseFloat(s.total_cash) || 0;
  const totalAssets = parseFloat(s.total_assets) || 0;
  const totalLiabilities = Math.abs(parseFloat(s.total_liabilities) || 0);
  const netWorthVal = parseFloat(s.net_worth) || 0;
  const monthlyIncome = parseFloat(s.monthly_income) || 0;
  const monthlyExpenses = Math.abs(parseFloat(s.monthly_expenses) || 0);
  const savingsRate = s.savings_rate != null ? s.savings_rate : (monthlyIncome > 0 ? ((monthlyIncome - monthlyExpenses) / monthlyIncome * 100) : 0);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Аналитика</h1>
          <p className="text-gray-500">Финансовые показатели и отчёты</p>
        </div>
      </div>

      <Tabs defaultValue="dashboard" className="space-y-6">
        <TabsList>
          <TabsTrigger value="dashboard">Обзор</TabsTrigger>
          <TabsTrigger value="cash-flow">Денежный поток</TabsTrigger>
          <TabsTrigger value="net-worth">Капитал</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Наличные</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalCash >= 0 ? '' : '−'}{formatRub(totalCash)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Активы</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalAssets >= 0 ? '' : '−'}{formatRub(totalAssets)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Обязательства</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">−{formatRub(totalLiabilities)}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Капитал</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${netWorthVal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {netWorthVal >= 0 ? '' : '−'}{formatRub(netWorthVal)}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Сводка за месяц</CardTitle>
              <CardDescription>Доходы, расходы и норма сбережений</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Доходы</p>
                  <p className="text-2xl font-bold text-green-600">{formatRub(monthlyIncome)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Расходы</p>
                  <p className="text-2xl font-bold text-red-600">−{formatRub(monthlyExpenses)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Сбережения</p>
                  <p className="text-2xl font-bold text-blue-600">{formatRub(monthlyIncome - monthlyExpenses)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Норма сбережений</p>
                  <p className="text-2xl font-bold text-purple-600">{Math.round(savingsRate)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cash-flow">
          <Card>
            <CardHeader>
              <CardTitle>Денежный поток</CardTitle>
              <CardDescription>Доходы и расходы по месяцам</CardDescription>
            </CardHeader>
            <CardContent>
              <CashFlowChart data={cashFlow.data} isLoading={cashFlow.isLoading} isError={cashFlow.isError} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="net-worth">
          <Card>
            <CardHeader>
              <CardTitle>Динамика капитала</CardTitle>
              <CardDescription>Изменение капитала за последние 12 месяцев</CardDescription>
            </CardHeader>
            <CardContent>
              <NetWorthChart data={netWorth.data} isLoading={netWorth.isLoading} isError={netWorth.isError} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
