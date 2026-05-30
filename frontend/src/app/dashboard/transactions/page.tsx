'use client';

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';

export default function TransactionsPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Транзакции</h1>
          <p className="text-gray-500">Просмотр и управление транзакциями</p>
        </div>
        <Button href="/dashboard/transactions/new">Добавить транзакцию</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Последние транзакции</CardTitle>
            <CardDescription>50 последних операций</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <div>
                  <p className="font-medium">Зарплата</p>
                  <p className="text-sm text-muted-foreground">20 апреля 2026</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-green-600">+₽420 000</p>
                  <Badge variant="outline">Доход</Badge>
                </div>
              </div>

              <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <div>
                  <p className="font-medium">Пятёрочка</p>
                  <p className="text-sm text-muted-foreground">18 апреля 2026</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-red-600">−₽12 550</p>
                  <Badge variant="outline">Расход</Badge>
                </div>
              </div>

              <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <div>
                  <p className="font-medium">Электричество</p>
                  <p className="text-sm text-muted-foreground">15 апреля 2026</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-red-600">−₽8 920</p>
                  <Badge variant="outline">Расход</Badge>
                </div>
              </div>

              <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <div>
                  <p className="font-medium">Перевод в накопления</p>
                  <p className="text-sm text-muted-foreground">10 апреля 2026</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-red-600">−₽150 000</p>
                  <Badge variant="outline">Перевод</Badge>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button variant="outline" className="w-full">Все транзакции</Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Фильтры</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="date">Период</Label>
              <select id="date" className="w-full p-2 border rounded">
                <option>Последние 30 дней</option>
                <option>Последние 90 дней</option>
                <option>Текущий год</option>
              </select>
            </div>

            <div>
              <Label htmlFor="account">Счёт</Label>
              <select id="account" className="w-full p-2 border rounded">
                <option>Все счета</option>
                <option>Основной счёт</option>
                <option>Накопительный счёт</option>
                <option>Кредитная карта</option>
              </select>
            </div>

            <div>
              <Label htmlFor="category">Категория</Label>
              <select id="category" className="w-full p-2 border rounded">
                <option>Все категории</option>
                <option>Зарплата</option>
                <option>Продукты</option>
                <option>Коммунальные</option>
                <option>Транспорт</option>
              </select>
            </div>

            <div>
              <Label htmlFor="type">Тип</Label>
              <select id="type" className="w-full p-2 border rounded">
                <option>Все типы</option>
                <option>Доход</option>
                <option>Расход</option>
                <option>Перевод</option>
              </select>
            </div>

            <Button className="w-full">Применить фильтры</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
