import { getCompanyBySlug, getAllSlugs } from "@/lib/data";
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
    title: `${name} - AI Company Directory`,
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

  return <CompanyDetail company={company} locale={locale as Locale} dict={dict} />;
}
