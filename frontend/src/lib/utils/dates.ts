export function formatDate(dateString: string): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function formatDateTime(dateString: string): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getDatePresets() {
  const today = new Date();
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  const monthAgo = new Date(today);
  monthAgo.setMonth(monthAgo.getMonth() - 1);

  const quarterAgo = new Date(today);
  quarterAgo.setMonth(quarterAgo.getMonth() - 3);

  return {
    today: {
      from: today.toISOString().split('T')[0],
      to: today.toISOString().split('T')[0],
    },
    lastWeek: {
      from: weekAgo.toISOString().split('T')[0],
      to: today.toISOString().split('T')[0],
    },
    lastMonth: {
      from: monthAgo.toISOString().split('T')[0],
      to: today.toISOString().split('T')[0],
    },
    lastQuarter: {
      from: quarterAgo.toISOString().split('T')[0],
      to: today.toISOString().split('T')[0],
    },
  };
}
