'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useRegister } from '@/lib/api/queries/auth';

function errorMessage(error: unknown) {
  if (error && typeof error === 'object' && 'response' in error) {
    const response = (error as { response?: { data?: { error?: { message?: string }; detail?: string } } }).response;
    return response?.data?.error?.message || response?.data?.detail || 'Не удалось зарегистрироваться';
  }
  return 'Не удалось зарегистрироваться';
}

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [baseCurrency, setBaseCurrency] = useState(process.env.NEXT_PUBLIC_DEFAULT_CURRENCY || 'RUB');
  const [timezone, setTimezone] = useState(process.env.NEXT_PUBLIC_DEFAULT_TIMEZONE || 'Europe/Moscow');
  const [error, setError] = useState('');
  const register = useRegister();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    try {
      await register.mutateAsync({
        email,
        password,
        firstName,
        lastName,
        baseCurrency,
        timezone,
      });
      router.push('/dashboard');
      router.refresh();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">Регистрация</h1>
        <p className="text-gray-500 mt-2">Создайте аккаунт в ФинДокторе</p>
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

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="firstName">Имя</Label>
            <Input
              id="firstName"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="lastName">Фамилия</Label>
            <Input
              id="lastName"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </div>
        </div>

        <div>
          <Label htmlFor="password">Пароль</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <p className="text-xs text-gray-400 mt-1">Минимум 8 символов</p>
        </div>

        <div>
          <Label htmlFor="confirmPassword">Подтверждение пароля</Label>
          <Input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>

        <div>
          <Label htmlFor="baseCurrency">Основная валюта</Label>
          <Input
            id="baseCurrency"
            value={baseCurrency}
            onChange={(e) => setBaseCurrency(e.target.value)}
            required
          />
        </div>

        <div>
          <Label htmlFor="timezone">Часовой пояс</Label>
          <Input
            id="timezone"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            required
          />
        </div>

        <Button type="submit" className="w-full" disabled={register.isLoading}>
          {register.isLoading ? 'Создаём аккаунт...' : 'Зарегистрироваться'}
        </Button>
      </form>

      <div className="text-center text-sm text-gray-500">
        <p>Уже есть аккаунт? <a href="/auth/login" className="text-blue-600 hover:underline">Войти</a></p>
      </div>
    </div>
  );
}
