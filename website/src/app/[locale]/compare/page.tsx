import { getAllCompanies } from "@/lib/data";
import { getDictionary } from "@/lib/i18n";
import { ComparePageClient } from "./ComparePageClient";
import type { Locale } from "@/lib/types";

export default async function ComparePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const dict = await getDictionary(locale as Locale);
  const { companies } = getAllCompanies();

  return (
    <ComparePageClient
      companies={companies}
      locale={locale as Locale}
      dict={dict}
    />
  );
}
