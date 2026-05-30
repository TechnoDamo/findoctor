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

function safeStorageGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeStorageSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Ignore storage failures (e.g. private/in-app browser restrictions).
  }
}

function safeStorageRemove(key: string) {
  try {
    localStorage.removeItem(key);
  } catch {
    // Ignore storage failures.
  }
}

function setSessionCookie() {
  document.cookie = `${AUTH_COOKIE_NAME}=1; path=/; max-age=${SESSION_MAX_AGE_SECONDS}; samesite=lax`;
}

function clearSessionCookie() {
  document.cookie = `${AUTH_COOKIE_NAME}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; samesite=lax`;
}

async function syncSessionCookie(method: "POST" | "DELETE") {
  try {
    await fetch("/api/auth/session", {
      method,
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    // Keep client-side fallback cookie/localStorage behavior when request fails.
  }
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  return safeParseUser(safeStorageGet(AUTH_USER_KEY));
}

export function createUser(user: StoredUser) {
  safeStorageSet(AUTH_USER_KEY, JSON.stringify(user));
}

export function hasRegisteredUser() {
  return getStoredUser() !== null;
}

export async function signInSession() {
  safeStorageSet(AUTH_SESSION_KEY, "1");
  setSessionCookie();
  await syncSessionCookie("POST");
}

export async function signOutSession() {
  safeStorageRemove(AUTH_SESSION_KEY);
  clearSessionCookie();
  await syncSessionCookie("DELETE");
}

export function hasLocalSession() {
  if (typeof window === "undefined") {
    return false;
  }

  return safeStorageGet(AUTH_SESSION_KEY) === "1";
}

export function hasAuthCookie() {
  if (typeof document === "undefined") {
    return false;
  }

  return document.cookie
    .split(";")
    .map((chunk) => chunk.trim())
    .some((chunk) => chunk.startsWith(`${AUTH_COOKIE_NAME}=`));
}

export function hasClientSession() {
  return hasLocalSession() || hasAuthCookie();
}
