"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { FundingLeaderEntry } from "@/lib/types";

interface FundingChartProps {
  data: FundingLeaderEntry[];
  title: string;
}

export function FundingChart({ data, title }: FundingChartProps) {
  const chartData = data.map((d) => ({
    name: d.name,
    funding: d.total_raised_usd / 1_000_000_000,
  }));

  return (
    <div>
      <h3 className="font-semibold text-lg mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 100 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tickFormatter={(v) => `$${v}B`} />
          <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value) => [`$${Number(value).toFixed(1)}B`, "Funding"]} />
          <Bar dataKey="funding" fill="#6366f1" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
