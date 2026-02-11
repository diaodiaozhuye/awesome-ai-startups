import type { Locale } from "./types";

const dictionaries = {
  en: () => import("../i18n/en.json").then((m) => m.default),
  zh: () => import("../i18n/zh.json").then((m) => m.default),
};

export async function getDictionary(locale: Locale) {
  return dictionaries[locale]();
}

export const locales: Locale[] = ["en", "zh"];
export const defaultLocale: Locale = "en";
