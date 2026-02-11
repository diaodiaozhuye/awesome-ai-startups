import { getCompanyBySlug, getAllSlugs, getCategories } from "@/lib/data";
import { getDictionary, locales } from "@/lib/i18n";
import { CompanyDetail } from "@/components/company/CompanyDetail";
import type { Locale } from "@/lib/types";
import type { Metadata } from "next";

export function generateStaticParams() {
  const slugs = getAllSlugs();
  const params: { locale: string; slug: string }[] = [];
  for (const locale of locales) {
    for (const slug of slugs) {
      params.push({ locale, slug });
    }
  }
  return params;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale, slug } = await params;
  const company = getCompanyBySlug(slug);
  const name = locale === "zh" && company.name_zh ? company.name_zh : company.name;
  return {
    title: `${name} - AI Product Data`,
    description: locale === "zh" && company.description_zh
      ? company.description_zh
      : company.description,
  };
}

export default async function CompanyPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;
  const company = getCompanyBySlug(slug);
  const dict = await getDictionary(locale as Locale);
  const categories = getCategories();
  const cat = categories.find((c) => c.id === company.category);
  const categoryLabel = cat ? (locale === "zh" ? cat.name_zh : cat.name) : undefined;

  return <CompanyDetail company={company} locale={locale as Locale} dict={dict} categoryLabel={categoryLabel} />;
}
