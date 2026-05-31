import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./achievements-page.module.css";

type AchievementStatus = "bronze" | "silver" | "gold" | "locked";

type Achievement = {
  id: string;
  title: string;
  level: string;
  description: string;
  status: AchievementStatus;
};

const achievements: Achievement[] = [
  {
    id: "cushion",
    title: "Финансовая подушка",
    level: "бронза",
    description: "Создал резерв, есть запас",
    status: "bronze",
  },
  {
    id: "discipline",
    title: "Финансовая дисциплина",
    level: "серебро",
    description: "Заходил 14 дней подряд",
    status: "silver",
  },
  {
    id: "patient",
    title: "Финансовый пациент",
    level: "золото",
    description: "Набрал рейтинг нагрузки\nниже 10",
    status: "gold",
  },
  {
    id: "coffee",
    title: "Кофеман",
    level: "-",
    description: "",
    status: "locked",
  },
];

function getBadgeClass(status: AchievementStatus) {
  if (status === "bronze") {
    return styles.badgeBronze;
  }

  if (status === "silver") {
    return styles.badgeSilver;
  }

  if (status === "gold") {
    return styles.badgeGold;
  }

  return styles.badgeLocked;
}

export function AchievementsPage() {
  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title="Достижения"
          leftHref={financeRoutes.home}
          leftIcon="back"
          prizeHref={financeRoutes.achievements}
          logoutHref="/login"
          titleClassName={styles.headerTitle}
        />

        <section className={styles.achievementsList} aria-label="Достижения">
          {achievements.map((achievement) => (
            <article className={styles.achievementCard} key={achievement.id}>
              <div className={styles.achievementText}>
                <h2 className={styles.achievementTitle}>{achievement.title}</h2>
                <p className={styles.achievementLevel}>{achievement.level}</p>
                {achievement.description ? <p className={styles.achievementDescription}>{achievement.description}</p> : null}
              </div>

              <span className={`${styles.achievementBadge} ${getBadgeClass(achievement.status)}`} aria-hidden="true" />
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
