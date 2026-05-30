"use client";

import { ChevronRight } from "lucide-react";
import { BadgeCheck, Phone } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import { BottomSheetModal } from "@/components/BottomSheetModal";
import { FinanceHeader } from "@/components/FinanceHeader";
import { financeRoutes } from "@/lib/financeRoutes";

import styles from "./profile-page.module.css";

type ModalType = "consultant" | "support" | "age" | "about" | null;

const consultantLevels = [
  { id: "anger-5", name: "Злобный дед", anger: "Злость - 5" },
  { id: "anger-4", name: "Злобный дед", anger: "Злость - 4" },
  { id: "anger-3", name: "Злобный дед", anger: "Злость - 3" },
  { id: "anger-2", name: "Злобный дед", anger: "Злость - 2" },
  { id: "anger-1", name: "Злобный дед", anger: "Злость - 1" },
];

export function ProfilePage() {
  const [openModal, setOpenModal] = useState<ModalType>(null);
  const [darkThemeEnabled, setDarkThemeEnabled] = useState(false);
  const [selectedConsultantIndex, setSelectedConsultantIndex] = useState(0);

  return (
    <main className={styles.page}>
      <div className={styles.content}>
        <FinanceHeader
          title="Профиль"
          leftHref={financeRoutes.home}
          leftIcon="back"
          prizeHref={financeRoutes.achievements}
          logoutHref="/login"
        />

        <section className={styles.profileCard} aria-label="Статус заполнения профиля">
          <p className={styles.profileText}>
            Вы заполнили
            <br />
            профиль на
          </p>
          <p className={styles.profileValue}>75%</p>
        </section>

        <section className={styles.statsCard} aria-label="Консультант">
          <button type="button" className={styles.cardActionButton} onClick={() => setOpenModal("consultant")}>
            <span className={styles.consultantLabel}>Мой консультант</span>
            <span className={styles.consultantValueWrap}>
              <span className={styles.consultantName}>Злобный дед</span>
              <span className={styles.consultantValue}>Злость - 5</span>
            </span>
          </button>
        </section>

        <section className={styles.menuSection} aria-label="Тесты">
          <h2 className={styles.sectionTitle}>Тесты</h2>

          <button type="button" className={styles.testCardButton} onClick={() => setOpenModal("age")}>
            <span className={styles.testTitle}>
              Какой твой
              <br />
              финансовые возраст
            </span>
            <span className={styles.doneBadge} aria-hidden="true">
              <Image src="/icons/profile/check.svg" alt="" width={24} height={19} />
            </span>
          </button>

          <Link className={styles.testCardLink} href={financeRoutes.financialHealth}>
            <span className={styles.testTitle}>
              Твое финансовое
              <br />
              здоровье
            </span>
            <span className={styles.emptyBadge} aria-hidden="true" />
          </Link>
        </section>

        <section className={styles.aboutSection} aria-label="Обо мне">
          <h2 className={styles.sectionTitle}>Обо мне</h2>

          <div className={styles.aboutCard}>
            <p className={styles.aboutText}>
              На этой неделе предлагаю уменьшить
              <br />
              лимит на день до 1 500 руб, так как это
              <br />
              позволит добиться цели на 4 мес
              <br />
              быстрее
            </p>

            <button type="button" className={styles.detailsButton} onClick={() => setOpenModal("about")}>
              Подробнее
            </button>
          </div>
        </section>

        <section className={styles.settingsSection} aria-label="Настройки и разделы">
          <button type="button" className={styles.menuItemButton} onClick={() => setDarkThemeEnabled((prev) => !prev)}>
            <span className={styles.menuItemLeft}>
              <Image src="/icons/profile/night-mode.svg" alt="" width={27} height={27} />
              <span className={styles.menuItemLabel}>Темная тема</span>
            </span>

            <span className={`${styles.toggleTrack} ${darkThemeEnabled ? styles.toggleTrackActive : ""}`} aria-hidden="true">
              <span className={`${styles.toggleThumb} ${darkThemeEnabled ? styles.toggleThumbActive : ""}`} />
            </span>
          </button>

          <button type="button" className={styles.menuItemButton} onClick={() => setOpenModal("support")}>
            <span className={styles.menuItemLeft}>
              <Image src="/icons/profile/support.svg" alt="" width={27} height={27} />
              <span className={styles.menuItemLabel}>Поддержка</span>
            </span>
            <ChevronRight size={34} strokeWidth={2.2} aria-hidden="true" />
          </button>

          <Link className={styles.menuItemLink} href={financeRoutes.history}>
            <span className={styles.menuItemLeft}>
              <Image src="/icons/profile/history.svg" alt="" width={27} height={27} />
              <span className={styles.menuItemLabel}>История финансов</span>
            </span>
            <ChevronRight size={34} strokeWidth={2.2} aria-hidden="true" />
          </Link>
        </section>

      </div>

      <BottomSheetModal
        isOpen={openModal !== null}
        onClose={() => setOpenModal(null)}
        ariaLabel="Профиль модальное окно"
        backdropClassName={styles.profileBackdrop}
        sheetClassName={styles.profileModal}
        handleClassName={styles.profileHandle}
        titleClassName={styles.profileModalTitle}
        title={
          openModal === "consultant"
            ? "Мой консультант"
            : openModal === "support"
              ? "Поддержка"
            : openModal === "age"
              ? "Финансовый возраст"
              : openModal === "about"
                ? "Подробности"
                : undefined
        }
      >
        {openModal === "consultant" ? (
          <div className={styles.consultantModalContent}>
            {consultantLevels.map((level, index) => {
              const selected = index === selectedConsultantIndex;

              return (
                <button
                  type="button"
                  key={level.id}
                  className={styles.consultantOptionButton}
                  onClick={() => setSelectedConsultantIndex(index)}
                  aria-label={`${level.name}, ${level.anger}`}
                  aria-pressed={selected}
                >
                  <span className={styles.consultantOptionText}>
                    <span className={styles.consultantOptionName}>{level.name}</span>
                    <span className={styles.consultantOptionAnger}>{level.anger}</span>
                  </span>

                  <span className={selected ? styles.consultantOptionMarkActive : styles.consultantOptionMark} aria-hidden="true">
                    {selected ? <Image src="/icons/profile/check.svg" alt="" width={24} height={19} /> : null}
                  </span>
                </button>
              );
            })}
          </div>
        ) : null}

        {openModal === "support" ? (
          <div className={styles.supportModalContent}>
            <article className={styles.supportCard}>
              <p className={styles.supportRow}>
                <BadgeCheck size={24} strokeWidth={2.4} aria-hidden="true" />
                <span>Специалист - Александр</span>
              </p>

              <a className={styles.supportRowLink} href="tel:+79959324455" aria-label="Позвонить в поддержку +7 995 932 44 55">
                <Phone size={24} strokeWidth={2.4} aria-hidden="true" />
                <span>+7 995 932 44 55</span>
              </a>
            </article>
          </div>
        ) : null}

        {openModal === "age" || openModal === "about" ? (
          <div className={styles.modalContent}>
            {openModal === "age" ? <p>Раздел в разработке. Здесь будет тест финансового возраста.</p> : null}
            {openModal === "about" ? <p>Рекомендация: снизить дневной лимит до 1 500 руб и ускорить достижение цели на 4 месяца.</p> : null}
          </div>
        ) : null}
      </BottomSheetModal>
    </main>
  );
}
