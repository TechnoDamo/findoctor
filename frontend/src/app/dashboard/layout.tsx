export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
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
          </nav>
        </div>

        <div className="flex-1">
          <header className="bg-white border-b border-gray-200 p-4">
            <div className="flex justify-between items-center">
              <h1 className="text-xl font-semibold">ФинДоктор</h1>
              <div className="flex items-center space-x-4">
                <button className="text-gray-500 hover:text-gray-700 text-sm">Уведомления</button>
                <div className="w-8 h-8 rounded-full bg-gray-300"></div>
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
