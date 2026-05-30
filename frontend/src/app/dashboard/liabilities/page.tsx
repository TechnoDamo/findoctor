'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function LiabilitiesPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Обязательства</h1>
          <p className="text-gray-500">Кредиты, ипотека, долги</p>
        </div>
        <Button href="/dashboard/liabilities/new">Добавить обязательство</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Ипотека</CardTitle>
            <CardDescription>Сбербанк</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">−₽8 200 000</div>
            <p className="text-sm text-muted-foreground mt-2">Платёж: ₽85 000/мес</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Автокредит</CardTitle>
            <CardDescription>ВТБ</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">−₽1 200 000</div>
            <p className="text-sm text-muted-foreground mt-2">Платёж: ₽35 000/мес</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Кредитная карта</CardTitle>
            <CardDescription>Тинькофф</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">−₽87 525</div>
            <p className="text-sm text-muted-foreground mt-2">Мин. платёж: ₽5 000/мес</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Все обязательства</CardTitle>
          <CardDescription>Общий долг: ₽9 487 525</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { name: 'Ипотека', bank: 'Сбербанк', balance: '−₽8 200 000', payment: '₽85 000/мес', status: 'Активен' },
              { name: 'Автокредит', bank: 'ВТБ', balance: '−₽1 200 000', payment: '₽35 000/мес', status: 'Активен' },
              { name: 'Кредитная карта', bank: 'Тинькофф', balance: '−₽87 525', payment: '₽5 000/мес', status: 'Активна' },
            ].map((l, i) => (
              <div key={i} className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <div>
                  <p className="font-medium">{l.name}</p>
                  <p className="text-sm text-muted-foreground">{l.bank} • Платёж: {l.payment}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-red-600">{l.balance}</p>
                  <Badge variant="outline">{l.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
