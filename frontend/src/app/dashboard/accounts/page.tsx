'use client';

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function AccountsPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Счета</h1>
          <p className="text-gray-500">Управление банковскими счетами</p>
        </div>
        <Button href="/dashboard/accounts/new">Добавить счёт</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Основной счёт</CardTitle>
            <CardDescription>Дебетовая карта Сбербанк</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₽245 075</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Накопительный счёт</CardTitle>
            <CardDescription>Тинькофф накопления</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₽1 230 050</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Кредитная карта</CardTitle>
            <CardDescription>Visa Сбербанк</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">−₽87 525</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Все счета</CardTitle>
          <CardDescription>4 активных счёта</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div>
                <p className="font-medium">Основной счёт</p>
                <p className="text-sm text-muted-foreground">Дебетовая карта • RUB</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-green-600">₽245 075</p>
                <p className="text-sm text-muted-foreground">Сбербанк</p>
              </div>
            </div>

            <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div>
                <p className="font-medium">Накопительный счёт</p>
                <p className="text-sm text-muted-foreground">Вклад • RUB</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-green-600">₽1 230 050</p>
                <p className="text-sm text-muted-foreground">Тинькофф</p>
              </div>
            </div>

            <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div>
                <p className="font-medium">Кредитная карта</p>
                <p className="text-sm text-muted-foreground">Кредитная • RUB</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-red-600">−₽87 525</p>
                <p className="text-sm text-muted-foreground">Сбербанк</p>
              </div>
            </div>

            <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div>
                <p className="font-medium">Брокерский счёт</p>
                <p className="text-sm text-muted-foreground">Инвестиционный • USD</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-green-600">$5 200</p>
                <p className="text-sm text-muted-foreground">Interactive Brokers</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
