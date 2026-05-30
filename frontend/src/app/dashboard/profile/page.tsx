'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function ProfilePage() {
  const [firstName, setFirstName] = useState('Иван');
  const [lastName, setLastName] = useState('Иванов');
  const [email, setEmail] = useState('ivan@example.com');
  const [phone, setPhone] = useState('+7 999 123-45-67');
  const [currency, setCurrency] = useState('RUB');
  const [timezone, setTimezone] = useState('Europe/Moscow');
  const [country, setCountry] = useState('RU');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Профиль</h1>
        <p className="text-gray-500">Настройки аккаунта</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Личные данные</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName">Имя</Label>
                <Input id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="lastName">Фамилия</Label>
                <Input id="lastName" value={lastName} onChange={(e) => setLastName(e.target.value)} />
              </div>
            </div>
            <div>
              <Label htmlFor="email">Почта</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="phone">Телефон</Label>
              <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="currency">Основная валюта</Label>
                <select id="currency" className="w-full p-2 border rounded" value={currency} onChange={(e) => setCurrency(e.target.value)}>
                  <option value="RUB">RUB — Российский рубль</option>
                  <option value="USD">USD — Доллар США</option>
                  <option value="EUR">EUR — Евро</option>
                </select>
              </div>
              <div>
                <Label htmlFor="country">Страна</Label>
                <select id="country" className="w-full p-2 border rounded" value={country} onChange={(e) => setCountry(e.target.value)}>
                  <option value="RU">Россия</option>
                  <option value="KZ">Казахстан</option>
                  <option value="BY">Беларусь</option>
                  <option value="GE">Грузия</option>
                </select>
              </div>
            </div>
            <div>
              <Label htmlFor="timezone">Часовой пояс</Label>
              <select id="timezone" className="w-full p-2 border rounded" value={timezone} onChange={(e) => setTimezone(e.target.value)}>
                <option value="Europe/Moscow">Москва (UTC+3)</option>
                <option value="Asia/Yekaterinburg">Екатеринбург (UTC+5)</option>
                <option value="Asia/Novosibirsk">Новосибирск (UTC+7)</option>
              </select>
            </div>
            <Button type="submit">Сохранить</Button>
          </form>
        </CardContent>
      </Card>

      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">Опасная зона</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 mb-4">Удаление аккаунта необратимо. Все данные будут утеряны.</p>
          <Button variant="destructive">Удалить аккаунт</Button>
        </CardContent>
      </Card>
    </div>
  );
}
