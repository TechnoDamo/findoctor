import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Finance Next",
  description: "Финансовый фронтенд на Next.js",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
