import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FundingBadge } from "./FundingBadge";
import { formatCurrency } from "@/lib/utils";
import type { Company, Locale } from "@/lib/types";

interface CompanyDetailProps {
  company: Company;
  locale: Locale;
  dict: any;
}

export function CompanyDetail({ company, locale, dict }: CompanyDetailProps) {
  const t = dict.company;
  const basePath = "/ai-company-directory";
  const name = locale === "zh" && company.name_zh ? company.name_zh : company.name;
  const description = locale === "zh" && company.description_zh
    ? company.description_zh
    : company.description;

  return (
    <div className="max-w-4xl mx-auto">
      <Link
        href={`${basePath}/${locale}`}
        className="text-sm text-primary hover:underline mb-6 inline-block"
      >
        &larr; {t.back_to_list}
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold">{name}</h1>
          <p className="text-muted-foreground mt-2 text-lg">{description}</p>
        </div>
        <a
          href={company.website}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          {t.visit_website}
        </a>
      </div>

      {/* Tags */}
      {company.tags && company.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-8">
          <Badge variant="primary">{company.category.replace(/-/g, " ")}</Badge>
          {company.tags.map((tag) => (
            <Badge key={tag}>{tag}</Badge>
          ))}
          {company.open_source && <Badge variant="success">{t.open_source}</Badge>}
          {company.status && company.status !== "active" && (
            <Badge variant="warning">{company.status}</Badge>
          )}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Overview */}
        <Card>
          <h2 className="font-semibold text-lg mb-4">Overview</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">{t.founded}</dt>
              <dd className="font-medium">{company.founded_year}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">{t.headquarters}</dt>
              <dd className="font-medium">
                {company.headquarters.city}
                {company.headquarters.state && `, ${company.headquarters.state}`}
                , {company.headquarters.country}
              </dd>
            </div>
            {company.team?.employee_count_range && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t.employees}</dt>
                <dd className="font-medium">{company.team.employee_count_range}</dd>
              </div>
            )}
            {company.status && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t.status}</dt>
                <dd className="font-medium capitalize">{company.status}</dd>
              </div>
            )}
          </dl>
        </Card>

        {/* Funding */}
        {company.funding && (
          <Card>
            <h2 className="font-semibold text-lg mb-4">{t.funding}</h2>
            <dl className="space-y-3 text-sm">
              {company.funding.total_raised_usd !== undefined && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">{t.total_raised}</dt>
                  <dd className="font-medium text-lg">
                    {formatCurrency(company.funding.total_raised_usd)}
                  </dd>
                </div>
              )}
              {company.funding.last_round && (
                <div className="flex justify-between items-center">
                  <dt className="text-muted-foreground">{t.last_round}</dt>
                  <dd><FundingBadge round={company.funding.last_round} /></dd>
                </div>
              )}
              {company.funding.valuation_usd !== undefined && company.funding.valuation_usd > 0 && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">{t.valuation}</dt>
                  <dd className="font-medium">{formatCurrency(company.funding.valuation_usd)}</dd>
                </div>
              )}
              {company.funding.investors && company.funding.investors.length > 0 && (
                <div>
                  <dt className="text-muted-foreground mb-2">{t.investors}</dt>
                  <dd className="flex flex-wrap gap-1">
                    {company.funding.investors.map((inv) => (
                      <Badge key={inv}>{inv}</Badge>
                    ))}
                  </dd>
                </div>
              )}
            </dl>
          </Card>
        )}

        {/* Team */}
        {company.team?.founders && company.team.founders.length > 0 && (
          <Card>
            <h2 className="font-semibold text-lg mb-4">{t.team}</h2>
            <ul className="space-y-3">
              {company.team.founders.map((f) => (
                <li key={f.name} className="flex items-center justify-between text-sm">
                  <span className="font-medium">{f.name}</span>
                  <span className="text-muted-foreground">{f.title}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* Products */}
        {company.products && company.products.length > 0 && (
          <Card>
            <h2 className="font-semibold text-lg mb-4">{t.products}</h2>
            <ul className="space-y-3">
              {company.products.map((p) => (
                <li key={p.name} className="text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{p.name}</span>
                    {p.url && (
                      <a
                        href={p.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline text-xs"
                      >
                        Visit
                      </a>
                    )}
                  </div>
                  {p.description && (
                    <p className="text-muted-foreground mt-0.5">{p.description}</p>
                  )}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* Social Links */}
        {company.social && (
          <Card>
            <h2 className="font-semibold text-lg mb-4">{t.social}</h2>
            <div className="flex flex-wrap gap-3 text-sm">
              {company.social.github && (
                <a href={company.social.github} target="_blank" rel="noopener noreferrer"
                   className="text-primary hover:underline">GitHub</a>
              )}
              {company.social.twitter && (
                <span className="text-muted-foreground">{company.social.twitter}</span>
              )}
              {company.social.linkedin && (
                <a href={company.social.linkedin} target="_blank" rel="noopener noreferrer"
                   className="text-primary hover:underline">LinkedIn</a>
              )}
              {company.social.crunchbase && (
                <a href={company.social.crunchbase} target="_blank" rel="noopener noreferrer"
                   className="text-primary hover:underline">Crunchbase</a>
              )}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
