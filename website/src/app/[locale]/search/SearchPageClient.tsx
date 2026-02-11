"use client";

import { useState, useCallback, useMemo } from "react";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { FilterPanel } from "@/components/search/FilterPanel";
import { createSearchIndex } from "@/lib/search";
import type { CompanyIndexEntry, Locale, Category } from "@/lib/types";

interface SearchPageClientProps {
  companies: CompanyIndexEntry[];
  categories: Category[];
  countries: string[];
  locale: Locale;
  dict: any;
}

export function SearchPageClient({
  companies,
  categories,
  countries,
  locale,
  dict,
}: SearchPageClientProps) {
  const [query, setQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  const searchIndex = useMemo(() => createSearchIndex(companies), [companies]);

  const results = useMemo(() => {
    let filtered = companies;

    if (query.trim()) {
      const searchResults = searchIndex.search(query);
      filtered = searchResults.map((r) => r.item);
    }

    if (selectedCategory) {
      filtered = filtered.filter((c) => c.category === selectedCategory);
    }

    if (selectedCountry) {
      filtered = filtered.filter((c) => c.country === selectedCountry);
    }

    return filtered;
  }, [companies, query, selectedCategory, selectedCountry, searchIndex]);

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
        noResultsText={dict.search.no_results}
        resultsText={dict.search.results}
      />
    </div>
  );
}
