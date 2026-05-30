const DEFAULT_BACKEND_BASE_URL = "https://napped-algorithm-theft.ngrok-free.dev";
const DEFAULT_AUTH_COOKIE_NAME = "findoctor_auth";
const DEFAULT_AUTH_USER_KEY = "findoctor_auth_user";
const DEFAULT_AUTH_SESSION_KEY = "findoctor_auth_session";
const DEFAULT_AUTH_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function getStringEnv(value: string | undefined, fallback: string): string {
  if (typeof value !== "string") {
    return fallback;
  }

  const trimmedValue = value.trim();

  return trimmedValue.length > 0 ? trimmedValue : fallback;
}

function getPositiveIntEnv(value: string | undefined, fallback: number): number {
  if (typeof value !== "string") {
    return fallback;
  }

  const parsed = Number.parseInt(value, 10);

  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }

  return parsed;
}

export const appConfig = {
  backend: {
    baseUrl: trimTrailingSlash(
      getStringEnv(process.env.NEXT_PUBLIC_BACKEND_URL, DEFAULT_BACKEND_BASE_URL),
    ),
  },
  auth: {
    cookieName: getStringEnv(process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME, DEFAULT_AUTH_COOKIE_NAME),
    userStorageKey: getStringEnv(process.env.NEXT_PUBLIC_AUTH_USER_KEY, DEFAULT_AUTH_USER_KEY),
    sessionStorageKey: getStringEnv(
      process.env.NEXT_PUBLIC_AUTH_SESSION_KEY,
      DEFAULT_AUTH_SESSION_KEY,
    ),
    sessionMaxAgeSeconds: getPositiveIntEnv(
      process.env.NEXT_PUBLIC_AUTH_SESSION_MAX_AGE_SECONDS,
      DEFAULT_AUTH_SESSION_MAX_AGE_SECONDS,
    ),
  },
} as const;
