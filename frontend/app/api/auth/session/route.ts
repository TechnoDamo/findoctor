import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME } from "@/lib/auth";
import { appConfig } from "@/lib/config";

const SESSION_MAX_AGE_SECONDS = appConfig.auth.sessionMaxAgeSeconds;

function getSecureFlag() {
  return process.env.NODE_ENV === "production";
}

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(AUTH_COOKIE_NAME, "1", {
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
    sameSite: "lax",
    secure: getSecureFlag(),
    httpOnly: false,
  });
  return response;
}

export async function DELETE() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(AUTH_COOKIE_NAME);
  return response;
}
