import { getAllCompanies, getCategories } from "@/lib/data";
import { getDictionary } from "@/lib/i18n";
import { SearchPageClient } from "./SearchPageClient";
import type { Locale } from "@/lib/types";

export default async function SearchPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const dict = await getDictionary(locale as Locale);
  const { companies } = getAllCompanies();
  const categories = getCategories();

  const countries = Array.from(
    new Set(companies.map((c) => c.country).filter(Boolean))
  ).sort();

  return (
    <SearchPageClient
      companies={companies}
      categories={categories}
      countries={countries}
      locale={locale as Locale}
      dict={dict}
    />
  );
}
