"use client";

import { useState, useMemo } from "react";
import { ProductCard } from "./ProductCard";
import { Pagination } from "@/components/ui/Pagination";
import { Button } from "@/components/ui/Button";
import { localized } from "@/lib/utils";
import type { ProductIndexEntry, Locale, Category } from "@/lib/types";
import type { HomeDict } from "@/lib/dict";

interface ProductGridProps {
  products: ProductIndexEntry[];
  categories: Category[];
  locale: Locale;
  dict: { home: HomeDict };
}

const ITEMS_PER_PAGE = 12;

export function ProductGrid({ products, categories, locale, dict }: ProductGridProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"funding" | "name">("funding");
  const [currentPage, setCurrentPage] = useState(1);

  const categoryMap = useMemo(
    () => new Map(categories.map((c) => [c.id, c])),
    [categories],
  );

  const filtered = useMemo(() => {
    let result = products;

    if (selectedCategory) {
      result = result.filter((p) => p.category === selectedCategory);
    }

    result = [...result].sort((a, b) => {
      switch (sortBy) {
        case "funding":
          return (b.total_raised_usd || 0) - (a.total_raised_usd || 0);
        case "name":
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

    return result;
  }, [products, selectedCategory, sortBy]);

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
          {dict.home.filter_all} ({products.length})
        </Button>
        {categories.map((cat) => {
          const count = products.filter((p) => p.category === cat.id).length;
          if (count === 0) return null;
          const label = localized(cat, locale, "name");
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
        {(["funding", "name"] as const).map((s) => (
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
          {paged.map((product) => {
            const cat = categoryMap.get(product.category);
            const catLabel = cat ? localized(cat, locale, "name") : undefined;
            return (
              <ProductCard key={product.slug} product={product} locale={locale} categoryLabel={catLabel} />
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
