"use client";

import { Button } from "@/components/ui/Button";
import { localized } from "@/lib/utils";
import type { Category, Locale } from "@/lib/types";

interface FilterPanelProps {
  categories: Category[];
  countries: string[];
  selectedCategory: string | null;
  selectedCountry: string | null;
  onCategoryChange: (cat: string | null) => void;
  onCountryChange: (country: string | null) => void;
  locale: Locale;
  dict: {
    search: {
      filters: string;
      category: string;
      country: string;
      clear_filters: string;
    };
  };
}

export function FilterPanel({
  categories,
  countries,
  selectedCategory,
  selectedCountry,
  onCategoryChange,
  onCountryChange,
  locale,
  dict,
}: FilterPanelProps) {
  const hasFilters = selectedCategory || selectedCountry;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-sm">{dict.search.filters}</h3>
        {hasFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              onCategoryChange(null);
              onCountryChange(null);
            }}
          >
            {dict.search.clear_filters}
          </Button>
        )}
      </div>

      {/* Category filter */}
      <div>
        <h4 className="text-xs font-medium text-muted-foreground mb-2">{dict.search.category}</h4>
        <div className="flex flex-wrap gap-1">
          {categories.map((cat) => (
            <Button
              key={cat.id}
              variant={selectedCategory === cat.id ? "default" : "outline"}
              size="sm"
              onClick={() =>
                onCategoryChange(selectedCategory === cat.id ? null : cat.id)
              }
            >
              {localized(cat, locale, "name")}
            </Button>
          ))}
        </div>
      </div>

      {/* Country filter */}
      <div>
        <h4 className="text-xs font-medium text-muted-foreground mb-2">{dict.search.country}</h4>
        <div className="flex flex-wrap gap-1">
          {countries.map((country) => (
            <Button
              key={country}
              variant={selectedCountry === country ? "default" : "outline"}
              size="sm"
              onClick={() =>
                onCountryChange(selectedCountry === country ? null : country)
              }
            >
              {country}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
