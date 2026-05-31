import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'ПрофИИт — Вход',
  description: 'Авторизация и регистрация',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {children}
      </div>
    </div>
  );
}