"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { StatEntry } from "@/lib/types";

interface FoundedTimelineProps {
  data: StatEntry[];
  title: string;
}

export function FoundedTimeline({ data, title }: FoundedTimelineProps) {
  const chartData = data
    .map((d) => ({ year: parseInt(d.label), count: d.count }))
    .sort((a, b) => a.year - b.year);

  return (
    <div>
      <h3 className="font-semibold text-lg mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="count"
            stroke="#6366f1"
            strokeWidth={2}
            dot={{ fill: "#6366f1" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
