import { CompanyCard } from "@/components/company/CompanyCard";
import type { CompanyIndexEntry, Locale, Category } from "@/lib/types";

interface SearchResultsProps {
  results: CompanyIndexEntry[];
  locale: Locale;
  categories?: Category[];
  noResultsText: string;
  resultsText: string;
}

export function SearchResults({ results, locale, categories, noResultsText, resultsText }: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-12">{noResultsText}</p>
    );
  }

  return (
    <div>
      <p className="text-sm text-muted-foreground mb-4">
        {resultsText.replace("{count}", String(results.length))}
      </p>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((company) => {
          const cat = categories?.find((c) => c.id === company.category);
          const catLabel = cat ? (locale === "zh" ? cat.name_zh : cat.name) : undefined;
          return (
            <CompanyCard key={company.slug} company={company} locale={locale} categoryLabel={catLabel} />
          );
        })}
      </div>
    </div>
  );
}
