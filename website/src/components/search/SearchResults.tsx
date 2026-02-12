import { useMemo } from "react";
import { ProductCard } from "@/components/product/ProductCard";
import { localized } from "@/lib/utils";
import type { ProductIndexEntry, Locale, Category } from "@/lib/types";

interface SearchResultsProps {
  results: ProductIndexEntry[];
  locale: Locale;
  categories: Category[];
  noResultsText: string;
  resultsText: string;
}

export function SearchResults({ results, locale, categories, noResultsText, resultsText }: SearchResultsProps) {
  const categoryMap = useMemo(
    () => new Map(categories.map((c) => [c.id, c])),
    [categories],
  );

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
        {results.map((product) => {
          const cat = categoryMap.get(product.category);
          const catLabel = cat ? localized(cat, locale, "name") : undefined;
          return (
            <ProductCard key={product.slug} product={product} locale={locale} categoryLabel={catLabel} />
          );
        })}
      </div>
    </div>
  );
}
