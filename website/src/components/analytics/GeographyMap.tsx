"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { StatEntry } from "@/lib/types";

interface GeographyMapProps {
  data: StatEntry[];
  title: string;
}

export function GeographyMap({ data, title }: GeographyMapProps) {
  const chartData = data.map((d) => ({
    country: d.label,
    count: d.count,
  }));

  return (
    <div>
      <h3 className="font-semibold text-lg mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="country" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
