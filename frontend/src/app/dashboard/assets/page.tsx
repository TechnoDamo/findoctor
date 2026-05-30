'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function AssetsPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Активы</h1>
          <p className="text-gray-500">Имущество, инвестиции и ценности</p>
        </div>
        <Button href="/dashboard/assets/new">Добавить актив</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Квартира</CardTitle>
            <CardDescription>Недвижимость</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₽12 500 000</div>
            <p className="text-sm text-muted-foreground mt-2">Куплена: март 2020</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Автомобиль</CardTitle>
            <CardDescription>Транспорт</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₽2 800 000</div>
            <p className="text-sm text-muted-foreground mt-2">Куплен: июнь 2023</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Инвестпортфель</CardTitle>
            <CardDescription>Ценные бумаги</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₽1 500 000</div>
            <p className="text-sm text-muted-foreground mt-2">Ежемесячный взнос: ₽50 000</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Все активы</CardTitle>
          <CardDescription>Общая стоимость: ₽16 800 000</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { name: 'Квартира', type: 'Недвижимость', value: '₽12 500 000', date: 'Март 2020' },
              { name: 'Автомобиль', type: 'Транспорт', value: '₽2 800 000', date: 'Июнь 2023' },
              { name: 'Инвестпортфель', type: 'Ценные бумаги', value: '₽1 500 000', date: 'Январь 2022' },
            ].map((a, i) => (
              <div key={i} className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <div>
                  <p className="font-medium">{a.name}</p>
                  <p className="text-sm text-muted-foreground">{a.type} • {a.date}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-green-600">{a.value}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
