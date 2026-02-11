export function formatCurrency(amount: number): string {
  if (amount >= 1_000_000_000) {
    return `$${(amount / 1_000_000_000).toFixed(1)}B`;
  }
  if (amount >= 1_000_000) {
    return `$${(amount / 1_000_000).toFixed(0)}M`;
  }
  if (amount >= 1_000) {
    return `$${(amount / 1_000).toFixed(0)}K`;
  }
  return `$${amount}`;
}

export function formatRound(round: string): string {
  const map: Record<string, string> = {
    "pre-seed": "Pre-Seed",
    seed: "Seed",
    "series-a": "Series A",
    "series-b": "Series B",
    "series-c": "Series C",
    "series-d": "Series D",
    "series-e": "Series E",
    "series-f": "Series F",
    growth: "Growth",
    ipo: "IPO",
    unknown: "Unknown",
  };
  return map[round] || round;
}

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
