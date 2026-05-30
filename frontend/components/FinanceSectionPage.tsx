import Link from "next/link";

import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./finance.module.css";

type FinanceSectionPageProps = {
  title: string;
  subtitle: string;
  amount?: string;
};

export function FinanceSectionPage({ title, subtitle, amount }: FinanceSectionPageProps) {
  return (
    <main className={styles.financeScreen}>
      <div className={styles.contentWrap}>
        <FinanceHeader title="Профиит" leftHref={financeRoutes.home} leftIcon="back" prizeHref={financeRoutes.achievements} logoutHref="/login" />

        <section className={styles.detailCard}>
          <p className={styles.detailSubtitle}>{subtitle}</p>
          <h2 className={styles.detailTitle}>{title}</h2>
          {amount ? <p className={styles.detailAmount}>{amount}</p> : null}
          <p className={styles.detailText}>Страница подключена к URL-навигации Next.js и готова под бизнес-логику.</p>
          <Link className={styles.detailBackLink} href={financeRoutes.home}>
            Вернуться на главный экран
          </Link>
        </section>
      </div>
    </main>
  );
}
