import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FundingBadge } from "./FundingBadge";
import { formatCurrency, localized } from "@/lib/utils";
import type { ProductIndexEntry, Locale } from "@/lib/types";

interface ProductCardProps {
  product: ProductIndexEntry;
  locale: Locale;
  categoryLabel?: string;
}

export function ProductCard({ product, locale, categoryLabel }: ProductCardProps) {
  const name = localized(product, locale, "name");
  const description = localized(product, locale, "description");

  return (
    <Link href={`/${locale}/products/${product.slug}`}>
      <Card hover className="h-full flex flex-col">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="font-semibold text-lg">{name}</h3>
            {product.company_name && (
              <p className="text-xs text-muted-foreground">{product.company_name}</p>
            )}
          </div>
          {product.open_source && (
            <Badge variant="success">OSS</Badge>
          )}
        </div>

        <p className="text-sm text-muted-foreground mt-2 line-clamp-2 flex-grow">
          {description}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant="primary">{categoryLabel || product.category.replace(/-/g, " ")}</Badge>
          {product.product_type && (
            <Badge>{product.product_type}</Badge>
          )}
          {product.last_round && <FundingBadge round={product.last_round} />}
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
          <span>{product.country}</span>
          <span>
            {product.total_raised_usd > 0
              ? formatCurrency(product.total_raised_usd)
              : product.status}
          </span>
        </div>
      </Card>
    </Link>
  );
}
