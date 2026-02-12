import { getProductBySlug, getAllSlugs, getCategories } from "@/lib/data";
import { getDictionary, locales } from "@/lib/i18n";
import { ProductDetail } from "@/components/product/ProductDetail";
import { localized } from "@/lib/utils";
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
  const product = getProductBySlug(slug);
  const name = localized(product, locale as Locale, "name");
  const description = localized(product, locale as Locale, "description");
  return {
    title: `${name} - AI Product Data`,
    description,
  };
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;
  const product = getProductBySlug(slug);
  const dict = await getDictionary(locale as Locale);
  const categories = getCategories();
  const cat = categories.find((c) => c.id === product.category);
  const categoryLabel = cat ? localized(cat, locale as Locale, "name") : undefined;

  return <ProductDetail product={product} locale={locale as Locale} dict={dict} categoryLabel={categoryLabel} />;
}
