"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { createUser, getStoredUser, hasClientSession, signInSession } from "@/lib/authStorage";

import styles from "./auth.module.css";

type AuthMode = "login" | "register";

type AuthFormProps = {
  mode: AuthMode;
};

const LABELS: Record<AuthMode, { title: string; switchText: string; switchHref: string }> = {
  login: {
    title: "Авторизация",
    switchText: "Еще нет аккаунта",
    switchHref: "/register",
  },
  register: {
    title: "Регистрация",
    switchText: "Уже есть аккаунт",
    switchHref: "/login",
  },
};

function normalizeEmail(value: string) {
  return value.trim().toLowerCase();
}

export function AuthForm({ mode }: AuthFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreed, setAgreed] = useState(mode === "register");
  const [error, setError] = useState("");

  const currentLabel = LABELS[mode];

  useEffect(() => {
    if (hasClientSession()) {
      window.location.replace("/finance");
    }
  }, []);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedEmail = normalizeEmail(email);

    if (!normalizedEmail || !password.trim()) {
      setError("Заполните почту и пароль");
      return;
    }

    if (!agreed) {
      setError("Подтвердите согласие с условиями");
      return;
    }

    const storedUser = getStoredUser();

    if (mode === "register") {
      if (storedUser && storedUser.email === normalizedEmail) {
        setError("Этот email уже занят");
        return;
      }

      createUser({ email: normalizedEmail, password });
      await signInSession();
      window.location.assign("/finance");
      return;
    }

    if (!storedUser) {
      setError("Аккаунт не найден. Зарегистрируйтесь.");
      return;
    }

    if (storedUser.email !== normalizedEmail || storedUser.password !== password) {
      setError("Неверная почта или пароль");
      return;
    }

    await signInSession();
    window.location.assign("/finance");
  };

  return (
    <main className={styles.authScreen}>
      <div className={styles.authWrap}>
        <h1 className={styles.brandTitle}>Профиит</h1>
        <p className={styles.brandSubtitle}>Помогаем смотреть в будущее</p>

        <h2 className={styles.formTitle}>{currentLabel.title}</h2>

        <form onSubmit={onSubmit}>
          <div className={styles.fieldCard}>
            <input
              className={styles.field}
              type="email"
              autoComplete="email"
              placeholder="Почта"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                setError("");
              }}
            />
            <input
              className={styles.field}
              type="password"
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              placeholder="Пароль"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                setError("");
              }}
            />
          </div>

          <Link className={styles.switchLink} href={currentLabel.switchHref}>
            {currentLabel.switchText}
          </Link>

          <div className={styles.agreementRow}>
            <label
              className={styles.checkControl}
              data-checked={agreed}
            >
              <input
                className={styles.checkInput}
                type="checkbox"
                checked={agreed}
                onChange={(event) => {
                  setAgreed(event.target.checked);
                  setError("");
                }}
                aria-label="Согласие с условиями"
              />
              <span className={styles.checkIcon} aria-hidden="true">
                ✓
              </span>
            </label>
            <p className={styles.agreementText}>
              Нажимая кнопку «Продолжить» я соглашаюсь с условиями пользовательского соглашения и подтверждаю, что мне
              исполнилось 18 лет
            </p>
          </div>

          <p className={styles.errorMessage} aria-live="polite">
            {error}
          </p>

          <button className={styles.submitButton} type="submit" onTouchStart={() => {}}>
            Продолжить
          </button>
        </form>
      </div>
    </main>
  );
}
