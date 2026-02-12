import { getAllProducts, getCategories } from "@/lib/data";
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
  const { products } = getAllProducts();
  const categories = getCategories();

  const countries = Array.from(
    new Set(products.map((p) => p.country).filter(Boolean))
  ).sort();

  return (
    <SearchPageClient
      products={products}
      categories={categories}
      countries={countries}
      locale={locale as Locale}
      dict={dict}
    />
  );
}
