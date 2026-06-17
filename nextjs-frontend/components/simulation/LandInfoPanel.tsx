"use client";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { type LandInfoData } from "@/lib/definitions";

type Props = {
  data: LandInfoData | null;
  loading: boolean;
};

function SkeletonRow() {
  return <div className="h-4 bg-dalock-surface rounded animate-pulse mb-2" />;
}

function formatPrice(pricePerSqm: number): string {
  const manwon = Math.round(pricePerSqm / 10000);
  return `${manwon.toLocaleString("ko-KR")}만원`;
}

export default function LandInfoPanel({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2 pt-1">
        <SkeletonRow />
        <SkeletonRow />
        <div className="h-24 bg-dalock-surface rounded animate-pulse mt-3" />
      </div>
    );
  }

  if (!data) return null;

  if ("error" in data) {
    return <p className="text-xs text-dalock-text2">{data.error}</p>;
  }

  const latestYear = data.price_history.at(-1)?.year ?? parseInt(data.std_year);

  return (
    <div className="space-y-4">
      {/* 현재 공시지가 */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-dalock-surface rounded-lg p-3">
          <p className="text-xs text-dalock-text2">공시지가 ({data.std_year})</p>
          <p className="text-sm font-semibold mt-0.5 text-dalock-text1">
            {formatPrice(data.current_price_per_sqm)}
            <span className="text-xs font-normal text-dalock-text2">/㎡</span>
          </p>
        </div>
        <div className="bg-dalock-surface rounded-lg p-3">
          <p className="text-xs text-dalock-text2">토지면적</p>
          <p className="text-sm font-semibold mt-0.5 text-dalock-text1">
            {data.land_area_sqm.toLocaleString("ko-KR", { maximumFractionDigits: 0 })}
            <span className="text-xs font-normal text-dalock-text2">㎡</span>
          </p>
        </div>
      </div>

      {data.land_type && (
        <p className="text-xs text-dalock-text2">
          지목: <span className="text-dalock-text1 font-medium">{data.land_type}</span>
        </p>
      )}

      {/* 연도별 공시지가 추이 */}
      {data.price_history.length > 1 && (
        <div>
          <p className="text-xs font-semibold text-dalock-text2 mb-2">
            연도별 공시지가 추이
          </p>
          <ResponsiveContainer width="100%" height={100}>
            <BarChart data={data.price_history} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis
                dataKey="year"
                tick={{ fontSize: 10, fill: "#94A3B8" }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 9, fill: "#94A3B8" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${Math.round(v / 10000)}만`}
              />
              <Tooltip
                formatter={(v: number) => [`${formatPrice(v)}/㎡`, "공시지가"]}
                labelFormatter={(label) => `${label}년`}
                contentStyle={{ fontSize: 11 }}
              />
              <Bar dataKey="price_per_sqm" radius={[2, 2, 0, 0]}>
                {data.price_history.map((entry) => (
                  <Cell
                    key={entry.year}
                    fill={entry.year === latestYear ? "#2563EB" : "#93C5FD"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
