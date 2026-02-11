"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { StatEntry } from "@/lib/types";

interface CategoryDistributionProps {
  data: StatEntry[];
  title: string;
}

const COLORS = [
  "#6366f1", "#8b5cf6", "#a855f7", "#d946ef",
  "#ec4899", "#f43f5e", "#f97316", "#eab308",
  "#84cc16", "#22c55e", "#14b8a6", "#06b6d4",
  "#3b82f6", "#6b7280", "#78716c", "#71717a",
  "#64748b",
];

export function CategoryDistribution({ data, title }: CategoryDistributionProps) {
  const chartData = data.map((d) => ({
    name: d.label.replace(/-/g, " ").replace(/\bai\b/g, "AI"),
    value: d.count,
  }));

  return (
    <div>
      <h3 className="font-semibold text-lg mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            outerRadius={120}
            dataKey="value"
            label={({ name, value }) => `${name} (${value})`}
          >
            {chartData.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
