import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FundingBadge } from "./FundingBadge";
import { formatCurrency } from "@/lib/utils";
import type { CompanyIndexEntry, Locale } from "@/lib/types";

interface CompanyCardProps {
  company: CompanyIndexEntry;
  locale: Locale;
}

export function CompanyCard({ company, locale }: CompanyCardProps) {
  const basePath = "/ai-company-directory";
  const name = locale === "zh" && company.name_zh ? company.name_zh : company.name;
  const description = locale === "zh" && company.description_zh
    ? company.description_zh
    : company.description;

  return (
    <Link href={`${basePath}/${locale}/companies/${company.slug}`}>
      <Card hover className="h-full flex flex-col">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-lg">{name}</h3>
          {company.open_source && (
            <Badge variant="success">OSS</Badge>
          )}
        </div>

        <p className="text-sm text-muted-foreground mt-2 line-clamp-2 flex-grow">
          {description}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant="primary">{company.category.replace(/-/g, " ")}</Badge>
          {company.last_round && <FundingBadge round={company.last_round} />}
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
          <span>{company.country}</span>
          <span>
            {company.total_raised_usd > 0
              ? formatCurrency(company.total_raised_usd)
              : `Est. ${company.founded_year}`}
          </span>
        </div>
      </Card>
    </Link>
  );
}
