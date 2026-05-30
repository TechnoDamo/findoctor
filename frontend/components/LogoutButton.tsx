"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";

import { signOutSession } from "@/lib/authStorage";

import styles from "./finance.module.css";

type LogoutButtonProps = {
  href: string;
  className?: string;
};

export function LogoutButton({ href, className }: LogoutButtonProps) {
  const router = useRouter();

  return (
    <button
      type="button"
      className={[styles.circleAction, styles.circleActionButton, className].filter(Boolean).join(" ")}
      aria-label="Выйти"
      onClick={() => {
        signOutSession();
        router.push(href);
        router.refresh();
      }}
    >
      <Image src="/icons/log-out.svg" alt="" width={21} height={21} />
    </button>
  );
}
