"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/types";

interface LanguageSwitcherProps {
  locale: Locale;
}

function GlobeIcon() {
  return (
    <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M2 12h20" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

export function LanguageSwitcher({ locale }: LanguageSwitcherProps) {
  const pathname = usePathname();

  const buildPath = (target: Locale) =>
    pathname.replace(/^\/(en|zh)(?=\/|$)/, `/${target}`);

  return (
    <nav
      className="inline-flex items-center rounded-full border border-border bg-muted/50 p-0.5 text-sm"
      aria-label="Language"
    >
      <Link
        href={buildPath("en")}
        aria-current={locale === "en" ? "page" : undefined}
        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 transition-colors ${
          locale === "en"
            ? "bg-primary text-primary-foreground font-medium shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <GlobeIcon />
        EN
      </Link>
      <Link
        href={buildPath("zh")}
        aria-current={locale === "zh" ? "page" : undefined}
        className={`inline-flex items-center rounded-full px-2.5 py-1 transition-colors ${
          locale === "zh"
            ? "bg-primary text-primary-foreground font-medium shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        中文
      </Link>
    </nav>
  );
}
