"use client";
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { type ComparisonEntry } from "@/lib/definitions";

type ChartEntry = { name: string; monthly_revenue: number; isTarget: boolean };

type Props = {
  data: ComparisonEntry[];
  targetRevenue: number;
};

export default function ComparisonBarChart({ data, targetRevenue }: Props) {
  const chartData: ChartEntry[] = [
    { name: "분석 대상", monthly_revenue: targetRevenue, isTarget: true },
    ...data.map((d) => ({ ...d, isTarget: false })),
  ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart
        data={chartData}
        margin={{ top: 8, right: 8, left: 8, bottom: 28 }}
      >
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11, fill: "#64748B" }}
          tickLine={false}
          axisLine={false}
          interval={0}
          angle={-20}
          textAnchor="end"
        />
        <Tooltip
          formatter={(value) =>
            typeof value === "number"
              ? [`${Math.round(value / 10_000).toLocaleString("ko-KR")}만원`, "예상 월매출"]
              : [String(value), "예상 월매출"]
          }
          contentStyle={{ borderRadius: "8px", fontSize: "12px" }}
        />
        <Bar dataKey="monthly_revenue" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.isTarget ? "#2563EB" : "#BFDBFE"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
