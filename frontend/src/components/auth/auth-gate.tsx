'use client';

import { useEffect, useMemo } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useCurrentUser, useLogout } from '@/lib/api/queries/auth';
import { getStoredAccessToken, useAuthStore } from '@/lib/auth/auth-store';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const hydrateFromStorage = useAuthStore((state) => state.hydrateFromStorage);
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user as { email?: string; first_name?: string | null } | null);
  const logout = useLogout();

  useEffect(() => {
    hydrateFromStorage();
  }, [hydrateFromStorage]);

  useEffect(() => {
    if (!getStoredAccessToken()) {
      router.replace(`/auth/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [pathname, router]);

  const currentUser = useCurrentUser(Boolean(accessToken));

  useEffect(() => {
    if (currentUser.isError) {
      router.replace(`/auth/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [currentUser.isError, pathname, router]);

  const displayName = useMemo(() => {
    if (!user) return '';
    return user.first_name || user.email || '';
  }, [user]);

  if (!accessToken || currentUser.isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 grid place-items-center p-6">
        <div className="text-sm text-gray-500">Проверяем сессию...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        <div className="w-64 bg-white border-r border-gray-200 min-h-screen p-4">
          <div className="text-xl font-bold mb-8 text-primary">ФинДоктор</div>
          <nav className="space-y-1">
            <a href="/dashboard" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm font-medium">Обзор</a>
            <a href="/dashboard/accounts" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">Счета</a>
            <a href="/dashboard/transactions" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">Транзакции</a>
            <a href="/dashboard/transfers" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">Переводы</a>
            <a href="/dashboard/assets" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">Активы</a>
            <a href="/dashboard/liabilities" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">Обязательства</a>
            <a href="/dashboard/goals" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">Цели</a>
            <a href="/dashboard/analytics" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">Аналитика</a>
            <a href="/dashboard/ai-chat" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">AI-ассистент</a>
            <a href="/dashboard/profile" className="block px-4 py-2 rounded hover:bg-gray-100 text-sm">Профиль</a>
          </nav>
        </div>

        <div className="flex-1">
          <header className="bg-white border-b border-gray-200 p-4">
            <div className="flex justify-between items-center">
              <h1 className="text-xl font-semibold">ФинДоктор</h1>
              <div className="flex items-center space-x-4">
                {displayName && <span className="text-sm text-gray-600">{displayName}</span>}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={logout.isLoading}
                  onClick={() => logout.mutate(undefined, { onSettled: () => router.replace('/auth/login') })}
                >
                  Выйти
                </Button>
              </div>
            </div>
          </header>

          <main className="p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
