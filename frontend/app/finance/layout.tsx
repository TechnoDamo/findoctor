"use client";

import { useEffect } from "react";

import { hasClientSession } from "@/lib/authStorage";

export default function FinanceLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  useEffect(() => {
    if (!hasClientSession()) {
      window.location.assign("/login");
    }
  }, []);

  return children;
}
