"use client";

import Image from "next/image";
import { useMemo, useState, type ChangeEvent, type FormEvent } from "react";

import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./financial-history-page.module.css";

type OperationDirection = "expense" | "income";

type HistoryItem = {
  id: string;
  type: string;
  name: string;
  amountRub: number;
  direction: OperationDirection;
};

type HistoryGroup = {
  date: string;
  items: HistoryItem[];
};

const historyGroups: HistoryGroup[] = [
  {
    date: "29 мая",
    items: [
      {
        id: "29-1",
        type: "Обязательные расходы",
        name: "Детям на сладкое",
        amountRub: 2000,
        direction: "expense",
      },
      {
        id: "29-2",
        type: "Необязательные расходы",
        name: "Подписки на GPT",
        amountRub: 7000,
        direction: "expense",
      },
      {
        id: "29-3",
        type: "Постоянный доход",
        name: "Подписки на GPT",
        amountRub: 7000,
        direction: "income",
      },
      {
        id: "29-4",
        type: "Непостоянный доход",
        name: "Подписки на GPT",
        amountRub: 7000,
        direction: "income",
      },
    ],
  },
  {
    date: "28 мая",
    items: [
      {
        id: "28-1",
        type: "Обязательные расходы",
        name: "Детям на сладкое",
        amountRub: 2000,
        direction: "expense",
      },
      {
        id: "28-2",
        type: "Необязательные расходы",
        name: "Подписки на GPT",
        amountRub: 7000,
        direction: "expense",
      },
    ],
  },
];

const amountFormatter = new Intl.NumberFormat("ru-RU");

function formatRubAmount(value: number) {
  return amountFormatter.format(value);
}

function normalizeQuery(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

export function FinancialHistoryPage() {
  const [query, setQuery] = useState("");

  const filteredHistoryGroups = useMemo(() => {
    const normalized = normalizeQuery(query);
    const compact = normalized.replace(/\s+/g, "");

    if (!normalized) {
      return historyGroups;
    }

    return historyGroups
      .map((group) => {
        const nextItems = group.items.filter((item) => {
          const amount = formatRubAmount(item.amountRub);
          const searchHaystack = `${group.date} ${item.type} ${item.name} ${amount} ${item.amountRub}`
            .toLowerCase()
            .replace(/\s+/g, " ");
          const compactAmount = amount.replace(/\s+/g, "");
          return searchHaystack.includes(normalized) || compactAmount.includes(compact) || String(item.amountRub).includes(compact);
        });

        return { ...group, items: nextItems };
      })
      .filter((group) => group.items.length > 0);
  }, [query]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  function handleQueryChange(event: ChangeEvent<HTMLInputElement>) {
    setQuery(event.target.value);
  }

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title={"История\nфинансов"}
          leftHref={financeRoutes.profile}
          leftIcon="back"
          prizeHref={financeRoutes.achievements}
          logoutHref="/login"
          titleClassName={styles.headerTitle}
        />

        <form className={styles.searchForm} onSubmit={handleSubmit}>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Поиск по финансам"
            value={query}
            onChange={handleQueryChange}
            aria-label="Поиск по финансам"
            autoComplete="off"
          />
        </form>

        <section className={styles.historySection} aria-label="История операций по дням">
          {filteredHistoryGroups.map((group) => (
            <div className={styles.group} key={group.date}>
              <h2 className={styles.dateTitle}>{group.date}</h2>

              <div className={styles.operationsList}>
                {group.items.map((item) => (
                  <article className={styles.operationCard} key={item.id}>
                    <div className={styles.operationInfo}>
                      <p className={styles.operationType}>{item.type}</p>
                      <p className={styles.operationName}>{item.name}</p>
                    </div>

                    <p className={styles.operationAmount}>
                      <strong>{formatRubAmount(item.amountRub)}</strong>
                      <span>руб</span>
                    </p>

                    <Image
                      className={styles.operationIcon}
                      src={item.direction === "income" ? "/icons/finance/history-income.svg" : "/icons/finance/history-expense.svg"}
                      alt=""
                      width={27}
                      height={27}
                      aria-hidden="true"
                    />
                  </article>
                ))}
              </div>
            </div>
          ))}

          {filteredHistoryGroups.length === 0 ? <p className={styles.noResults}>Ничего не найдено</p> : null}
        </section>
      </div>
    </main>
  );
}
