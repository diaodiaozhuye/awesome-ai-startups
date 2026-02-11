import Link from "next/link";
import { LanguageSwitcher } from "./LanguageSwitcher";
import type { Locale } from "@/lib/types";

interface HeaderProps {
  locale: Locale;
  dict: {
    nav: {
      home: string;
      search: string;
      compare: string;
      analytics: string;
      github: string;
    };
    site: { title: string };
  };
}

export function Header({ locale, dict }: HeaderProps) {
  const prefix = `/${locale}`;

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href={`${prefix}`} className="text-xl font-bold text-primary">
              {dict.site.title}
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link href={`${prefix}`} className="text-sm hover:text-primary transition-colors">
                {dict.nav.home}
              </Link>
              <Link href={`${prefix}/search`} className="text-sm hover:text-primary transition-colors">
                {dict.nav.search}
              </Link>
              <Link href={`${prefix}/compare`} className="text-sm hover:text-primary transition-colors">
                {dict.nav.compare}
              </Link>
              <Link href={`${prefix}/analytics`} className="text-sm hover:text-primary transition-colors">
                {dict.nav.analytics}
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <LanguageSwitcher locale={locale} />
            <a
              href="https://github.com/diaodiaozhuye/awesome-ai-startups"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {dict.nav.github}
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}
