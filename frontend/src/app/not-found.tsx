'use client';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-300">404</h1>
        <p className="text-xl text-gray-600 mt-4">Страница не найдена</p>
        <a href="/dashboard" className="text-blue-600 hover:underline mt-4 inline-block">Вернуться на главную</a>
      </div>
    </div>
  );
}
