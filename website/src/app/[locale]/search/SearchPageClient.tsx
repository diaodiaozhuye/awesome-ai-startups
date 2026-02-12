"use client";

import { useState, useCallback, useMemo } from "react";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { FilterPanel } from "@/components/search/FilterPanel";
import { createSearchIndex } from "@/lib/search";
import type { ProductIndexEntry, Locale, Category } from "@/lib/types";
import type { Dictionary } from "@/lib/dict";

interface SearchPageClientProps {
  products: ProductIndexEntry[];
  categories: Category[];
  countries: string[];
  locale: Locale;
  dict: Dictionary;
}

export function SearchPageClient({
  products,
  categories,
  countries,
  locale,
  dict,
}: SearchPageClientProps) {
  const [query, setQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  const searchIndex = useMemo(() => createSearchIndex(products), [products]);

  const results = useMemo(() => {
    let filtered = products;

    if (query.trim()) {
      const searchResults = searchIndex.search(query);
      filtered = searchResults.map((r) => r.item);
    }

    if (selectedCategory) {
      filtered = filtered.filter((p) => p.category === selectedCategory);
    }

    if (selectedCountry) {
      filtered = filtered.filter((p) => p.country === selectedCountry);
    }

    return filtered;
  }, [products, query, selectedCategory, selectedCountry, searchIndex]);

  const handleSearch = useCallback((q: string) => {
    setQuery(q);
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{dict.search.title}</h1>

      <div className="mb-6">
        <SearchBar
          placeholder={dict.search.placeholder}
          onSearch={handleSearch}
        />
      </div>

      <div className="mb-6">
        <FilterPanel
          categories={categories}
          countries={countries}
          selectedCategory={selectedCategory}
          selectedCountry={selectedCountry}
          onCategoryChange={setSelectedCategory}
          onCountryChange={setSelectedCountry}
          locale={locale}
          dict={dict}
        />
      </div>

      <SearchResults
        results={results}
        locale={locale}
        categories={categories}
        noResultsText={dict.search.no_results}
        resultsText={dict.search.results}
      />
    </div>
  );
}
