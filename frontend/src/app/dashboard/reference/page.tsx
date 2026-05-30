'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const categories = [
  { name: 'Зарплата', type: 'Доход' },
  { name: 'Фриланс', type: 'Доход' },
  { name: 'Инвестиции', type: 'Доход' },
  { name: 'Продукты', type: 'Расход' },
  { name: 'Транспорт', type: 'Расход' },
  { name: 'Жильё', type: 'Расход' },
  { name: 'Развлечения', type: 'Расход' },
  { name: 'Здоровье', type: 'Расход' },
];

const institutions = [
  { name: 'Сбербанк', country: 'RU', types: ['Банк', 'Брокер'] },
  { name: 'Тинькофф', country: 'RU', types: ['Банк', 'Брокер'] },
  { name: 'ВТБ', country: 'RU', types: ['Банк'] },
  { name: 'Interactive Brokers', country: 'US', types: ['Брокер'] },
];

const merchants = [
  { name: 'Пятёрочка', category: 'Продукты', risk: 'Низкий' },
  { name: 'Яндекс.Такси', category: 'Транспорт', risk: 'Низкий' },
  { name: 'Ozon', category: 'Товары', risk: 'Низкий' },
  { name: 'Мосэнерго', category: 'Жильё', risk: 'Низкий' },
];

export default function ReferencePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Справочники</h1>

      <Tabs defaultValue="categories">
        <TabsList>
          <TabsTrigger value="categories">Категории</TabsTrigger>
          <TabsTrigger value="institutions">Банки и брокеры</TabsTrigger>
          <TabsTrigger value="merchants">Мерчанты</TabsTrigger>
          <TabsTrigger value="types">Типы</TabsTrigger>
        </TabsList>

        <TabsContent value="categories">
          <Card>
            <CardHeader>
              <CardTitle>Категории транзакций</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {categories.map((c, i) => (
                  <div key={i} className="flex justify-between items-center p-3 border rounded-lg">
                    <span className="font-medium">{c.name}</span>
                    <span className={`text-sm px-2 py-1 rounded-full ${c.type === 'Доход' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{c.type}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="institutions">
          <Card>
            <CardHeader>
              <CardTitle>Финансовые организации</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {institutions.map((inst, i) => (
                  <div key={i} className="flex justify-between items-center p-3 border rounded-lg">
                    <div>
                      <span className="font-medium">{inst.name}</span>
                      <span className="text-sm text-muted-foreground ml-2">{inst.country}</span>
                    </div>
                    <div className="flex gap-1">
                      {inst.types.map((t, j) => (
                        <span key={j} className="text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded-full">{t}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="merchants">
          <Card>
            <CardHeader>
              <CardTitle>Мерчанты</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {merchants.map((m, i) => (
                  <div key={i} className="flex justify-between items-center p-3 border rounded-lg">
                    <div>
                      <span className="font-medium">{m.name}</span>
                      <span className="text-sm text-muted-foreground ml-2">{m.category}</span>
                    </div>
                    <span className="text-sm bg-gray-100 text-gray-700 px-2 py-1 rounded-full">{m.risk}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="types">
          <Card>
            <CardHeader>
              <CardTitle>Типы счетов</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {['Дебетовая карта', 'Кредитная карта', 'Накопительный', 'Вклад', 'Брокерский', 'Электронный кошелёк'].map((t, i) => (
                  <div key={i} className="p-3 border rounded-lg text-center font-medium hover:bg-gray-50 cursor-pointer">{t}</div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
