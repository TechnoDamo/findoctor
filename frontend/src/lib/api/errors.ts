export function apiErrorMessage(error: unknown, fallback: string) {
  if (!error || typeof error !== 'object') return fallback;

  const maybeAxiosError = error as {
    code?: string;
    message?: string;
    response?: {
      status?: number;
      data?: {
        error?: { message?: string };
        detail?: string | Array<{ msg?: string }>;
      };
    };
    request?: unknown;
  };

  const data = maybeAxiosError.response?.data;
  const detail = data?.detail;

  if (data?.error?.message) return data.error.message;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;

  if (maybeAxiosError.response?.status) {
    return `${fallback}: HTTP ${maybeAxiosError.response.status}`;
  }

  if (maybeAxiosError.code === 'ERR_NETWORK' || maybeAxiosError.request) {
    return `${fallback}: API недоступен. Проверьте NEXT_PUBLIC_API_URL и CORS.`;
  }

  return maybeAxiosError.message || fallback;
}
