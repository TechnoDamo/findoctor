import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./income-page.module.css";

type IncomeSource = {
  id: string;
  name: string;
  amount: string;
};

const incomeSources: IncomeSource[] = [
  { id: "dev-work", name: "Работа разработчика", amount: "150 000 руб" },
  { id: "freelance", name: "Фриланс", amount: "90 000 руб" },
];

export function IncomePage() {
  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title="Доходы"
          leftHref={financeRoutes.home}
          leftIcon="back"
          prizeHref={financeRoutes.profile}
          logoutHref="/login"
        />

        <section className={styles.summaryCard} aria-label="Сводка доходов">
          <div className={styles.summaryLeft}>
            <p className={styles.summaryLabel}>Ваш доход мес</p>
            <p className={styles.summaryValue}>
              <strong>240 000</strong>
              <span>руб</span>
            </p>
          </div>

          <div className={styles.expenseBadge}>
            <p className={styles.expenseLabel}>Расход</p>
            <p className={styles.expenseValue}>
              <strong>54 000</strong>
              <span>руб</span>
            </p>
          </div>
        </section>

        <section className={styles.sourcesSection} aria-label="Источники дохода">
          <div className={styles.sourcesHeader}>
            <h2 className={styles.sectionTitle}>Источники дохода</h2>
            <button className={styles.addButton} type="button" aria-label="Добавить источник дохода">
              +
            </button>
          </div>

          <div className={styles.sourcesList}>
            {incomeSources.map((source) => (
              <button className={styles.sourceCard} key={source.id} type="button" aria-label={`${source.name} ${source.amount}`}>
                <span className={styles.sourceName}>{source.name}</span>
                <span className={styles.sourceAmount}>{source.amount}</span>
              </button>
            ))}
          </div>
        </section>

        <section className={styles.recommendationSection} aria-label="Рекомендации">
          <h2 className={styles.sectionTitle}>Рекомендации</h2>

          <div className={styles.recommendationCard}>
            <p className={styles.recommendationText}>
              Учитывая доходы и расходы, вы получаете больше 2% населения, у вас очень мало расходов
            </p>

            <button className={styles.chatButton} type="button" aria-label="Продолжить в чате">
              Продолжить в чате
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
