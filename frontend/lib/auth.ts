import { appConfig } from "@/lib/config";

export const AUTH_COOKIE_NAME = appConfig.auth.cookieName;
export const AUTH_USER_KEY = appConfig.auth.userStorageKey;
export const AUTH_SESSION_KEY = appConfig.auth.sessionStorageKey;

export type StoredUser = {
  email: string;
  password: string;
};
