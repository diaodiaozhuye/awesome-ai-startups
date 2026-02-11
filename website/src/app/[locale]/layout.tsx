import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { getDictionary, locales } from "@/lib/i18n";
import type { Locale } from "@/lib/types";

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const dict = await getDictionary(locale as Locale);

  return (
    <div className="min-h-screen flex flex-col">
      <Header locale={locale as Locale} dict={dict} />
      <main className="flex-grow mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <Footer dict={dict} />
    </div>
  );
}
