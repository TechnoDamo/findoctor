import clsx from "clsx";
import { ArrowLeft } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { LogoutButton } from "@/components/LogoutButton";

import styles from "./finance.module.css";

type FinanceHeaderProps = {
  title: string;
  leftHref: string;
  leftIcon: "avatar" | "back";
  prizeHref?: string;
  logoutHref?: string;
  titleClassName?: string;
  headerClassName?: string;
  headerLeftClassName?: string;
  headerRightClassName?: string;
  actionClassName?: string;
};

export function FinanceHeader({
  title,
  leftHref,
  leftIcon,
  prizeHref,
  logoutHref,
  titleClassName,
  headerClassName,
  headerLeftClassName,
  headerRightClassName,
  actionClassName,
}: FinanceHeaderProps) {
  return (
    <header className={clsx(styles.header, headerClassName)}>
      <div className={clsx(styles.headerLeft, headerLeftClassName)}>
        <Link
          className={clsx(styles.circleAction, actionClassName)}
          href={leftHref}
          aria-label={leftIcon === "back" ? "Назад" : "Профиль"}
        >
          {leftIcon === "back" ? <ArrowLeft size={21} strokeWidth={2.4} /> : <Image src="/icons/avatar.svg" alt="" width={21} height={21} />}
        </Link>
        <h1
          className={[styles.headerTitle, titleClassName].filter(Boolean).join(" ")}
          style={title.includes("\n") ? { whiteSpace: "pre-line" } : undefined}
        >
          {title}
        </h1>
      </div>

      <div className={clsx(styles.headerRight, headerRightClassName)}>
        {prizeHref ? (
          <Link className={clsx(styles.circleAction, actionClassName)} href={prizeHref} aria-label="Достижения">
            <Image src="/icons/finance/prize.svg" alt="" width={21} height={21} />
          </Link>
        ) : null}
        {logoutHref ? <LogoutButton href={logoutHref} className={actionClassName} /> : null}
      </div>
    </header>
  );
}
