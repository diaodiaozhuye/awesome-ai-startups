import { getStats } from "@/lib/data";
import { getDictionary } from "@/lib/i18n";
import { formatCurrency } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { FundingChart } from "@/components/analytics/FundingChart";
import { CategoryDistribution } from "@/components/analytics/CategoryDistribution";
import { FoundedTimeline } from "@/components/analytics/FoundedTimeline";
import { GeographyMap } from "@/components/analytics/GeographyMap";
import type { Locale } from "@/lib/types";

export default async function AnalyticsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const dict = await getDictionary(locale as Locale);
  const stats = getStats();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">{dict.analytics.title}</h1>

      {/* Summary cards */}
      <div className="grid gap-6 sm:grid-cols-3 mb-12">
        <Card>
          <p className="text-sm text-muted-foreground">{dict.analytics.total_companies}</p>
          <p className="text-3xl font-bold mt-1">{stats.total_companies}</p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">{dict.analytics.total_funding}</p>
          <p className="text-3xl font-bold mt-1">{formatCurrency(stats.total_funding_usd)}</p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">{dict.analytics.open_source}</p>
          <p className="text-3xl font-bold mt-1">{stats.open_source_count}</p>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-8 lg:grid-cols-2">
        <Card>
          <FundingChart
            data={stats.funding_leaderboard}
            title={dict.analytics.funding_chart}
          />
        </Card>
        <Card>
          <CategoryDistribution
            data={stats.by_category}
            title={dict.analytics.category_chart}
          />
        </Card>
        <Card>
          <FoundedTimeline
            data={stats.by_founded_year}
            title={dict.analytics.timeline_chart}
          />
        </Card>
        <Card>
          <GeographyMap
            data={stats.by_country}
            title={dict.analytics.geography_chart}
          />
        </Card>
      </div>
    </div>
  );
}
