import { notFound } from "next/navigation";

import { CreditTrafficPage } from "@/components/CreditTrafficPage";
import { CushionModalPage } from "@/components/CushionModalPage";
import { DaySpendingPage } from "@/components/DaySpendingPage";
import { ExpensesPage } from "@/components/ExpensesPage";
import { IncomePage } from "@/components/IncomePage";
import { FinanceSectionPage } from "@/components/FinanceSectionPage";
import { ConsultantAudioPage } from "@/components/ConsultantAudioPage";
import { ConsultantTextPage } from "@/components/ConsultantTextPage";
import { ProfilePage } from "@/components/ProfilePage";
import { SavingsPage } from "@/components/SavingsPage";
import { financeSectionsBySlug } from "@/lib/financeSections";

type FinanceSectionRouteProps = {
  params: Promise<{ section: string }>;
  searchParams?: Promise<{ mode?: string | string[] }>;
};

export default async function FinanceSectionRoute({ params, searchParams }: FinanceSectionRouteProps) {
  const { section } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const sectionData = financeSectionsBySlug[section];

  if (!sectionData) {
    notFound();
  }

  if (section === "cushion_page") {
    return <CushionModalPage />;
  }

  if (section === "expenses_page") {
    return <ExpensesPage />;
  }

  if (section === "income_page") {
    return <IncomePage />;
  }

  if (section === "savings_page") {
    return <SavingsPage />;
  }

  if (section === "credit_traffic_page") {
    return <CreditTrafficPage />;
  }

  if (section === "consultant_page") {
    return <ConsultantTextPage />;
  }

  if (section === "consultant_audio_page") {
    return <ConsultantAudioPage />;
  }

  if (section === "profile_page") {
    return <ProfilePage />;
  }

  if (section === "day_spending_page") {
    const modeParam = resolvedSearchParams.mode;
    const modeValue = Array.isArray(modeParam) ? modeParam[0] : modeParam;
    const initialMode = modeValue === "income" ? "income" : "expense";

    return <DaySpendingPage initialMode={initialMode} />;
  }

  return <FinanceSectionPage title={sectionData.title} subtitle={sectionData.subtitle} amount={sectionData.amount} />;
}
