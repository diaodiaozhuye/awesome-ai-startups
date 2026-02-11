import { Badge } from "@/components/ui/Badge";
import { formatRound } from "@/lib/utils";

interface FundingBadgeProps {
  round: string;
}

const roundVariant: Record<string, "default" | "primary" | "success" | "warning"> = {
  "pre-seed": "default",
  seed: "default",
  "series-a": "primary",
  "series-b": "primary",
  "series-c": "primary",
  "series-d": "success",
  "series-e": "success",
  "series-f": "success",
  growth: "warning",
  ipo: "warning",
};

export function FundingBadge({ round }: FundingBadgeProps) {
  return (
    <Badge variant={roundVariant[round] || "default"}>
      {formatRound(round)}
    </Badge>
  );
}
