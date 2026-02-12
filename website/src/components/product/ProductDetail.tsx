import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FundingBadge } from "./FundingBadge";
import { formatCurrency, localized } from "@/lib/utils";
import type { ProductDetail as ProductDetailType, Locale } from "@/lib/types";
import type { Dictionary } from "@/lib/dict";

interface ProductDetailProps {
  product: ProductDetailType;
  locale: Locale;
  dict: Dictionary;
  categoryLabel?: string;
}

export function ProductDetail({ product, locale, dict, categoryLabel }: ProductDetailProps) {
  const t = dict.product;
  const name = localized(product, locale, "name");
  const description = localized(product, locale, "description");
  const company = product.company;

  return (
    <div className="max-w-4xl mx-auto">
      <Link
        href={`/${locale}`}
        className="text-sm text-primary hover:underline mb-6 inline-block"
      >
        &larr; {t.back_to_list}
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold">{name}</h1>
          {company?.name && (
            <p className="text-muted-foreground mt-1">
              {t.company_name}: {company.name}
            </p>
          )}
          <p className="text-muted-foreground mt-2 text-lg">{description}</p>
        </div>
        <a
          href={product.product_url}
          className="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          {t.visit_product}
        </a>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2 mb-8">
        <Badge variant="primary">{categoryLabel || product.category.replace(/-/g, " ")}</Badge>
        {product.product_type && (
          <Badge>{product.product_type}</Badge>
        )}
        {product.sub_category && (
          <Badge>{product.sub_category.replace(/-/g, " ")}</Badge>
        )}
        {product.tags && product.tags.map((tag) => (
          <Badge key={tag}>{tag}</Badge>
        ))}
        {product.open_source && <Badge variant="success">{t.open_source}</Badge>}
        {product.status && product.status !== "active" && (
          <Badge variant="warning">{product.status}</Badge>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Overview */}
        <Card>
          <h2 className="font-semibold text-lg mb-4">{t.overview}</h2>
          <dl className="space-y-3 text-sm">
            {product.product_type && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t.product_type}</dt>
                <dd className="font-medium">{product.product_type}</dd>
              </div>
            )}
            {product.status && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t.status}</dt>
                <dd className="font-medium capitalize">{product.status}</dd>
              </div>
            )}
            {company?.founded_year && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t.founded}</dt>
                <dd className="font-medium">{company.founded_year}</dd>
              </div>
            )}
            {company?.headquarters && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t.headquarters}</dt>
                <dd className="font-medium">
                  {company.headquarters.city}
                  {company.headquarters.state && `, ${company.headquarters.state}`}
                  , {company.headquarters.country}
                </dd>
              </div>
            )}
            {company?.employee_count_range && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t.employees}</dt>
                <dd className="font-medium">{company.employee_count_range}</dd>
              </div>
            )}
            {company?.website && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t.visit_company}</dt>
                <dd>
                  <a
                    href={company.website}
                    className="text-primary hover:underline text-sm"
                  >
                    {company.name}
                  </a>
                </dd>
              </div>
            )}
          </dl>
        </Card>

        {/* Funding */}
        {company?.funding && (
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

        {/* Key People */}
        {product.key_people && product.key_people.length > 0 && (
          <Card>
            <h2 className="font-semibold text-lg mb-4">{t.key_people}</h2>
            <ul className="space-y-3">
              {product.key_people.map((person) => (
                <li key={person.name} className="flex items-center justify-between text-sm">
                  <span className="font-medium">
                    {person.name}
                    {person.is_founder && (
                      <span className="ml-1 text-xs text-muted-foreground">({t.founder})</span>
                    )}
                  </span>
                  <span className="text-muted-foreground">{person.title}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {/* Social Links */}
        {company?.social && (
          <Card>
            <h2 className="font-semibold text-lg mb-4">{t.social}</h2>
            <div className="flex flex-wrap gap-3 text-sm">
              {company.social.github && (
                <a href={company.social.github}
                   className="text-primary hover:underline">GitHub</a>
              )}
              {company.social.twitter && (
                <a href={company.social.twitter}
                   className="text-primary hover:underline">Twitter</a>
              )}
              {company.social.linkedin && (
                <a href={company.social.linkedin}
                   className="text-primary hover:underline">LinkedIn</a>
              )}
              {company.social.crunchbase && (
                <a href={company.social.crunchbase}
                   className="text-primary hover:underline">Crunchbase</a>
              )}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
