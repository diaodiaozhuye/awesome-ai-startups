"use client";

import { useState, useMemo } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency, formatRound, localized } from "@/lib/utils";
import type { ProductIndexEntry, Locale } from "@/lib/types";
import type { Dictionary } from "@/lib/dict";

interface ComparePageClientProps {
  products: ProductIndexEntry[];
  locale: Locale;
  dict: Dictionary;
}

export function ComparePageClient({ products, locale, dict }: ComparePageClientProps) {
  const [selectedSlugs, setSelectedSlugs] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  const t = dict.product;
  const c = dict.compare;

  const selected = useMemo(
    () => products.filter((p) => selectedSlugs.includes(p.slug)),
    [products, selectedSlugs]
  );

  const searchResults = useMemo(() => {
    if (!searchTerm.trim()) return [];
    const term = searchTerm.toLowerCase();
    return products
      .filter(
        (p) =>
          !selectedSlugs.includes(p.slug) &&
          (p.name.toLowerCase().includes(term) ||
            (p.name_zh && p.name_zh.includes(term)))
      )
      .slice(0, 5);
  }, [products, searchTerm, selectedSlugs]);

  const addProduct = (slug: string) => {
    if (selectedSlugs.length < 3 && !selectedSlugs.includes(slug)) {
      setSelectedSlugs([...selectedSlugs, slug]);
      setSearchTerm("");
    }
  };

  const removeProduct = (slug: string) => {
    setSelectedSlugs(selectedSlugs.filter((s) => s !== slug));
  };

  const compareFields = [
    { key: "category", label: t.category, render: (p: ProductIndexEntry) => p.category.replace(/-/g, " ") },
    { key: "product_type", label: t.product_type, render: (p: ProductIndexEntry) => p.product_type || c.no_data },
    { key: "country", label: t.country, render: (p: ProductIndexEntry) => p.country },
    { key: "city", label: t.city, render: (p: ProductIndexEntry) => p.city },
    { key: "total_raised", label: t.total_raised, render: (p: ProductIndexEntry) => p.total_raised_usd ? formatCurrency(p.total_raised_usd) : c.no_data },
    { key: "valuation", label: t.valuation, render: (p: ProductIndexEntry) => p.valuation_usd ? formatCurrency(p.valuation_usd) : c.no_data },
    { key: "last_round", label: t.last_round, render: (p: ProductIndexEntry) => p.last_round ? formatRound(p.last_round) : c.no_data },
    { key: "employees", label: t.employees, render: (p: ProductIndexEntry) => p.employee_count_range || c.no_data },
    { key: "open_source", label: t.open_source, render: (p: ProductIndexEntry) => p.open_source ? t.yes : t.no },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{c.title}</h1>

      {selectedSlugs.length < 3 && (
        <div className="mb-6 relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={c.add_product}
            className="w-full max-w-md rounded-lg border border-border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          {searchResults.length > 0 && (
            <div className="absolute top-full left-0 mt-1 w-full max-w-md bg-background border border-border rounded-lg shadow-lg z-10">
              {searchResults.map((p) => (
                <button
                  key={p.slug}
                  onClick={() => addProduct(p.slug)}
                  className="block w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors"
                >
                  {localized(p, locale, "name")}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {selected.map((p) => (
            <Badge key={p.slug} variant="primary">
              {localized(p, locale, "name")}
              <button
                onClick={() => removeProduct(p.slug)}
                className="ml-2 hover:text-red-500"
              >
                x
              </button>
            </Badge>
          ))}
        </div>
      )}

      {selected.length >= 2 ? (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    {c.field}
                  </th>
                  {selected.map((p) => (
                    <th key={p.slug} className="text-left py-3 px-4 font-semibold">
                      {localized(p, locale, "name")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {compareFields.map((field) => (
                  <tr key={field.key} className="border-b border-border last:border-0">
                    <td className="py-3 px-4 text-muted-foreground">{field.label}</td>
                    {selected.map((p) => (
                      <td key={p.slug} className="py-3 px-4">
                        {field.render(p)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <p className="text-center text-muted-foreground py-12">
          {c.select_prompt}
        </p>
      )}
    </div>
  );
}
