'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

const goalsData = [
  { name: 'Подушка безопасности', target: 1000000, current: 650000, deadline: 'Декабрь 2026' },
  { name: 'На квартиру', target: 5000000, current: 1200000, deadline: 'Декабрь 2028' },
  { name: 'Отпуск', target: 500000, current: 380000, deadline: 'Август 2026' },
];

export default function GoalsPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Финансовые цели</h1>
          <p className="text-gray-500">Планирование и отслеживание целей</p>
        </div>
        <Button href="/dashboard/goals/new">Добавить цель</Button>
      </div>

      <div className="space-y-6">
        {goalsData.map((goal, i) => {
          const pct = Math.round((goal.current / goal.target) * 100);
          return (
            <Card key={i}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{goal.name}</CardTitle>
                    <CardDescription>Срок: {goal.deadline}</CardDescription>
                  </div>
                  <span className="text-lg font-bold">{pct}%</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <Progress value={pct} />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>₽{goal.current.toLocaleString('ru-RU')}</span>
                  <span>₽{goal.target.toLocaleString('ru-RU')}</span>
                </div>
                <Button variant="outline" size="sm">Подробнее</Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
