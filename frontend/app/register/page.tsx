import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AuthForm } from "@/components/AuthForm";
import { AUTH_COOKIE_NAME } from "@/lib/auth";

export default async function RegisterPage() {
  const cookieStore = await cookies();

  if (cookieStore.has(AUTH_COOKIE_NAME)) {
    redirect("/finance");
  }

  return <AuthForm mode="register" />;
}
