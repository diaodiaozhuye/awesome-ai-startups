"use client";

import { usePathname } from "next/navigation";
import type { Locale } from "@/lib/types";

interface LanguageSwitcherProps {
  locale: Locale;
}

export function LanguageSwitcher({ locale }: LanguageSwitcherProps) {
  const pathname = usePathname();
  const basePath = "/ai-company-directory";

  const switchTo = locale === "en" ? "zh" : "en";
  const newPath = pathname.replace(`${basePath}/${locale}`, `${basePath}/${switchTo}`);

  return (
    <a
      href={newPath}
      className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-muted transition-colors"
    >
      {locale === "en" ? "中文" : "English"}
    </a>
  );
}
