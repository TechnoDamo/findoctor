'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useGoals } from '@/lib/api/queries/goals';

function formatRub(value: number) {
  return `${value.toLocaleString('ru-RU')} ₽`;
}

export default function GoalsPage() {
  const router = useRouter();
  const { data: goals, isLoading, isError } = useGoals();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <Skeleton className="h-10 w-56" />
          <Skeleton className="h-10 w-40" />
        </div>
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32 w-full" />)}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Финансовые цели</h1>
        <Card><CardContent className="p-6 text-center text-red-500">Не удалось загрузить цели</CardContent></Card>
      </div>
    );
  }

  const goalsList = goals || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Финансовые цели</h1>
          <p className="text-gray-500">Планирование и отслеживание целей</p>
        </div>
        <Button onClick={() => router.push('/dashboard/goals/new')}>Добавить цель</Button>
      </div>

      {goalsList.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-gray-500">Пока нет целей. Добавьте первую.</CardContent></Card>
      ) : (
        <div className="space-y-4">
          {goalsList.map((goal) => {
            const pct = goal.target_amount > 0 ? Math.round((goal.current_amount / goal.target_amount) * 100) : 0;
            return (
              <Card key={goal.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle>{goal.name}</CardTitle>
                      {goal.deadline && (
                        <CardDescription>
                          До: {new Date(goal.deadline).toLocaleDateString('ru-RU')}
                        </CardDescription>
                      )}
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-bold">{formatRub(goal.current_amount)}</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{pct}%</span>
                      <span className="text-muted-foreground">{formatRub(goal.target_amount)}</span>
                    </div>
                    <Progress value={pct} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
