'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function TransfersPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Переводы</h1>
          <p className="text-gray-500">Переводы между счетами</p>
        </div>
        <Button href="/dashboard/transfers/new">Новый перевод</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>История переводов</CardTitle>
          <CardDescription>Последние операции</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div>
                <p className="font-medium">Основной → Накопительный</p>
                <p className="text-sm text-muted-foreground">10 апреля 2026</p>
              </div>
              <div className="text-right">
                <p className="font-bold">₽150 000</p>
                <p className="text-sm text-muted-foreground">RUB</p>
              </div>
            </div>
            <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div>
                <p className="font-medium">Основной → Брокерский</p>
                <p className="text-sm text-muted-foreground">5 апреля 2026</p>
              </div>
              <div className="text-right">
                <p className="font-bold">$500</p>
                <p className="text-sm text-muted-foreground">USD</p>
              </div>
            </div>
            <div className="flex justify-between items-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <div>
                <p className="font-medium">Накопительный → Основной</p>
                <p className="text-sm text-muted-foreground">1 апреля 2026</p>
              </div>
              <div className="text-right">
                <p className="font-bold">₽50 000</p>
                <p className="text-sm text-muted-foreground">RUB</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
