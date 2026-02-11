"use client";

import { useState, useMemo } from "react";
import { CompanyCard } from "./CompanyCard";
import { Pagination } from "@/components/ui/Pagination";
import { Button } from "@/components/ui/Button";
import type { CompanyIndexEntry, Locale, Category } from "@/lib/types";
import type { HomeDict } from "@/lib/dict";

interface CompanyGridProps {
  companies: CompanyIndexEntry[];
  categories: Category[];
  locale: Locale;
  dict: { home: HomeDict };
}

const ITEMS_PER_PAGE = 12;

export function CompanyGrid({ companies, categories, locale, dict }: CompanyGridProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"funding" | "name" | "year">("funding");
  const [currentPage, setCurrentPage] = useState(1);

  const categoryMap = useMemo(
    () => new Map(categories.map((c) => [c.id, c])),
    [categories],
  );

  const filtered = useMemo(() => {
    let result = companies;

    if (selectedCategory) {
      result = result.filter((c) => c.category === selectedCategory);
    }

    result = [...result].sort((a, b) => {
      switch (sortBy) {
        case "funding":
          return (b.total_raised_usd || 0) - (a.total_raised_usd || 0);
        case "name":
          return a.name.localeCompare(b.name);
        case "year":
          return (b.founded_year || 0) - (a.founded_year || 0);
        default:
          return 0;
      }
    });

    return result;
  }, [companies, selectedCategory, sortBy]);

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paged = filtered.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const handleCategoryChange = (cat: string | null) => {
    setSelectedCategory(cat);
    setCurrentPage(1);
  };

  return (
    <div>
      {/* Category filter tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        <Button
          variant={selectedCategory === null ? "default" : "outline"}
          size="sm"
          onClick={() => handleCategoryChange(null)}
        >
          {dict.home.filter_all} ({companies.length})
        </Button>
        {categories.map((cat) => {
          const count = companies.filter((c) => c.category === cat.id).length;
          if (count === 0) return null;
          const label = locale === "zh" ? cat.name_zh : cat.name;
          return (
            <Button
              key={cat.id}
              variant={selectedCategory === cat.id ? "default" : "outline"}
              size="sm"
              onClick={() => handleCategoryChange(cat.id)}
            >
              {label} ({count})
            </Button>
          );
        })}
      </div>

      {/* Sort controls */}
      <div className="flex items-center gap-2 mb-6 text-sm">
        <span className="text-muted-foreground">{dict.home.sort_by}:</span>
        {(["funding", "name", "year"] as const).map((s) => (
          <Button
            key={s}
            variant={sortBy === s ? "default" : "ghost"}
            size="sm"
            onClick={() => setSortBy(s)}
          >
            {dict.home[`sort_${s}`]}
          </Button>
        ))}
      </div>

      {/* Grid */}
      {paged.length === 0 ? (
        <p className="text-center text-muted-foreground py-12">{dict.home.no_results}</p>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {paged.map((company) => {
            const cat = categoryMap.get(company.category);
            const catLabel = cat ? (locale === "zh" ? cat.name_zh : cat.name) : undefined;
            return (
              <CompanyCard key={company.slug} company={company} locale={locale} categoryLabel={catLabel} />
            );
          })}
        </div>
      )}

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
    </div>
  );
}
