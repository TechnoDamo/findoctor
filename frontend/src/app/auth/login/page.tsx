'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useLogin } from '@/lib/api/queries/auth';

function errorMessage(error: unknown) {
  if (error && typeof error === 'object' && 'response' in error) {
    const response = (error as { response?: { data?: { error?: { message?: string }; detail?: string } } }).response;
    return response?.data?.error?.message || response?.data?.detail || 'Не удалось войти';
  }
  return 'Не удалось войти';
}

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const login = useLogin();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login.mutateAsync({ email, password });
      router.push('/dashboard');
      router.refresh();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">С возвращением</h1>
        <p className="text-gray-500 mt-2">Войдите в аккаунт</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="email">Почта</Label>
          <Input
            id="email"
            type="email"
            placeholder="ivan@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div>
          <Label htmlFor="password">Пароль</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <Button type="submit" className="w-full" disabled={login.isLoading}>
          {login.isLoading ? 'Входим...' : 'Войти'}
        </Button>
      </form>

      <div className="text-center text-sm text-gray-500">
        <p>Нет аккаунта? <a href="/auth/register" className="text-blue-600 hover:underline">Зарегистрироваться</a></p>
      </div>
    </div>
  );
}
