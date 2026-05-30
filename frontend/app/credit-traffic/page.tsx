import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { CreditTrafficPage } from "@/components/CreditTrafficPage";
import { AUTH_COOKIE_NAME } from "@/lib/auth";

export default async function CreditTrafficRoutePage() {
  const cookieStore = await cookies();

  if (!cookieStore.has(AUTH_COOKIE_NAME)) {
    redirect("/login");
  }

  return <CreditTrafficPage />;
}
