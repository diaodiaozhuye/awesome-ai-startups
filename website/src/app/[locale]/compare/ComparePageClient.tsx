"use client";

import { useState, useMemo } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency, formatRound } from "@/lib/utils";
import type { CompanyIndexEntry, Locale } from "@/lib/types";

interface ComparePageClientProps {
  companies: CompanyIndexEntry[];
  locale: Locale;
  dict: any;
}

export function ComparePageClient({ companies, locale, dict }: ComparePageClientProps) {
  const [selectedSlugs, setSelectedSlugs] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  const selected = useMemo(
    () => companies.filter((c) => selectedSlugs.includes(c.slug)),
    [companies, selectedSlugs]
  );

  const searchResults = useMemo(() => {
    if (!searchTerm.trim()) return [];
    const term = searchTerm.toLowerCase();
    return companies
      .filter(
        (c) =>
          !selectedSlugs.includes(c.slug) &&
          (c.name.toLowerCase().includes(term) ||
            (c.name_zh && c.name_zh.includes(term)))
      )
      .slice(0, 5);
  }, [companies, searchTerm, selectedSlugs]);

  const addCompany = (slug: string) => {
    if (selectedSlugs.length < 3 && !selectedSlugs.includes(slug)) {
      setSelectedSlugs([...selectedSlugs, slug]);
      setSearchTerm("");
    }
  };

  const removeCompany = (slug: string) => {
    setSelectedSlugs(selectedSlugs.filter((s) => s !== slug));
  };

  const compareFields = [
    { key: "category", label: locale === "zh" ? "分类" : "Category", render: (c: CompanyIndexEntry) => c.category.replace(/-/g, " ") },
    { key: "founded_year", label: locale === "zh" ? "成立年份" : "Founded", render: (c: CompanyIndexEntry) => String(c.founded_year) },
    { key: "country", label: locale === "zh" ? "国家" : "Country", render: (c: CompanyIndexEntry) => c.country },
    { key: "city", label: locale === "zh" ? "城市" : "City", render: (c: CompanyIndexEntry) => c.city },
    { key: "total_raised", label: locale === "zh" ? "总融资" : "Total Raised", render: (c: CompanyIndexEntry) => c.total_raised_usd ? formatCurrency(c.total_raised_usd) : "N/A" },
    { key: "valuation", label: locale === "zh" ? "估值" : "Valuation", render: (c: CompanyIndexEntry) => c.valuation_usd ? formatCurrency(c.valuation_usd) : "N/A" },
    { key: "last_round", label: locale === "zh" ? "最新轮次" : "Last Round", render: (c: CompanyIndexEntry) => c.last_round ? formatRound(c.last_round) : "N/A" },
    { key: "employees", label: locale === "zh" ? "员工" : "Employees", render: (c: CompanyIndexEntry) => c.employee_count_range || "N/A" },
    { key: "open_source", label: locale === "zh" ? "开源" : "Open Source", render: (c: CompanyIndexEntry) => c.open_source ? "Yes" : "No" },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{dict.compare.title}</h1>

      {selectedSlugs.length < 3 && (
        <div className="mb-6 relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={dict.compare.add_company}
            className="w-full max-w-md rounded-lg border border-border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          {searchResults.length > 0 && (
            <div className="absolute top-full left-0 mt-1 w-full max-w-md bg-background border border-border rounded-lg shadow-lg z-10">
              {searchResults.map((c) => (
                <button
                  key={c.slug}
                  onClick={() => addCompany(c.slug)}
                  className="block w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors"
                >
                  {locale === "zh" && c.name_zh ? c.name_zh : c.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {selected.map((c) => (
            <Badge key={c.slug} variant="primary">
              {locale === "zh" && c.name_zh ? c.name_zh : c.name}
              <button
                onClick={() => removeCompany(c.slug)}
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
                    {dict.compare.field}
                  </th>
                  {selected.map((c) => (
                    <th key={c.slug} className="text-left py-3 px-4 font-semibold">
                      {locale === "zh" && c.name_zh ? c.name_zh : c.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {compareFields.map((field) => (
                  <tr key={field.key} className="border-b border-border last:border-0">
                    <td className="py-3 px-4 text-muted-foreground">{field.label}</td>
                    {selected.map((c) => (
                      <td key={c.slug} className="py-3 px-4">
                        {field.render(c)}
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
          {dict.compare.select_prompt}
        </p>
      )}
    </div>
  );
}
