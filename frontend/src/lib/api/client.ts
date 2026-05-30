import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import {
  clearStoredAuth,
  getStoredAccessToken,
  getStoredRefreshToken,
  storeTokens,
} from '@/lib/auth/auth-store';

type RetriableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

type RefreshResponse = {
  access_token: string;
  refresh_token: string;
};

function apiBaseUrl() {
  const rawUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  const trimmedUrl = rawUrl.replace(/\/$/, '');
  return trimmedUrl.endsWith('/api/v1') ? trimmedUrl : `${trimmedUrl}/api/v1`;
}

const apiClient: AxiosInstance = axios.create({
  baseURL: apiBaseUrl(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept-Language': process.env.NEXT_PUBLIC_DEFAULT_LOCALE || 'ru',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = getStoredAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling auth errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const axiosError = error as AxiosError;
    const originalRequest = axiosError.config as RetriableRequestConfig | undefined;
    const requestUrl = originalRequest?.url || '';
    const isAuthEndpoint = requestUrl.includes('/auth/login') ||
      requestUrl.includes('/auth/register') ||
      requestUrl.includes('/auth/refresh');
    
    if (axiosError.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      const refreshToken = getStoredRefreshToken();
      if (!refreshToken) {
        clearStoredAuth();
        if (typeof window !== 'undefined') window.location.href = '/auth/login';
        return Promise.reject(error);
      }
      
      try {
        const response = await axios.post<RefreshResponse>(
          `${apiBaseUrl()}/auth/refresh`,
          { refresh_token: refreshToken },
          {
            headers: {
              'Content-Type': 'application/json',
              'Accept-Language': process.env.NEXT_PUBLIC_DEFAULT_LOCALE || 'ru',
            },
          }
        );

        storeTokens(response.data.access_token, response.data.refresh_token);
        originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        clearStoredAuth();
        if (typeof window !== 'undefined') window.location.href = '/auth/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export { apiBaseUrl };
export default apiClient;
