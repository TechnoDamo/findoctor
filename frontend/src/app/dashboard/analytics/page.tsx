'use client';

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CashFlowChart } from '@/components/charts/cash-flow-chart';
import { NetWorthChart } from '@/components/charts/net-worth-chart';

export default function AnalyticsPage() {
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
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z"/><path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"/><path d="M12 2v2"/><path d="M12 22v-2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₽1 245 000</div>
              </CardContent>
              <CardFooter>
                <p className="text-xs text-muted-foreground">+12,5% к прошлому месяцу</p>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Активы</CardTitle>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₽2 830 000</div>
              </CardContent>
              <CardFooter>
                <p className="text-xs text-muted-foreground">+8,7% к прошлому месяцу</p>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Обязательства</CardTitle>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">−₽1 520 000</div>
              </CardContent>
              <CardFooter>
                <p className="text-xs text-muted-foreground">−2,1% к прошлому месяцу</p>
              </CardFooter>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Капитал</CardTitle>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" className="h-4 w-4 text-muted-foreground"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 17l-5-5m10 0l-5 5"/></svg>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₽1 310 000</div>
              </CardContent>
              <CardFooter>
                <p className="text-xs text-muted-foreground">+15,6% к прошлому месяцу</p>
              </CardFooter>
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
                  <p className="text-2xl font-bold text-green-600">₽420 000</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Расходы</p>
                  <p className="text-2xl font-bold text-red-600">−₽285 000</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Сбережения</p>
                  <p className="text-2xl font-bold text-blue-600">₽135 000</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Норма сбережений</p>
                  <p className="text-2xl font-bold text-purple-600">32%</p>
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
              <CashFlowChart />
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
              <NetWorthChart />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
