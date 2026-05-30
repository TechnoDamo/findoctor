"use client";

import { AUTH_COOKIE_NAME, AUTH_SESSION_KEY, AUTH_USER_KEY, type StoredUser } from "@/lib/auth";
import { appConfig } from "@/lib/config";

const SESSION_MAX_AGE_SECONDS = appConfig.auth.sessionMaxAgeSeconds;

function safeParseUser(value: string | null): StoredUser | null {
  if (!value) {
    return null;
  }

  try {
    const parsed = JSON.parse(value) as Partial<StoredUser>;

    if (typeof parsed.email !== "string" || typeof parsed.password !== "string") {
      return null;
    }

    return { email: parsed.email, password: parsed.password };
  } catch {
    return null;
  }
}

function setSessionCookie() {
  document.cookie = `${AUTH_COOKIE_NAME}=1; path=/; max-age=${SESSION_MAX_AGE_SECONDS}; samesite=lax`;
}

function clearSessionCookie() {
  document.cookie = `${AUTH_COOKIE_NAME}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; samesite=lax`;
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  return safeParseUser(localStorage.getItem(AUTH_USER_KEY));
}

export function createUser(user: StoredUser) {
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function hasRegisteredUser() {
  return getStoredUser() !== null;
}

export function signInSession() {
  localStorage.setItem(AUTH_SESSION_KEY, "1");
  setSessionCookie();
}

export function signOutSession() {
  localStorage.removeItem(AUTH_SESSION_KEY);
  clearSessionCookie();
}

export function hasLocalSession() {
  if (typeof window === "undefined") {
    return false;
  }

  return localStorage.getItem(AUTH_SESSION_KEY) === "1";
}
