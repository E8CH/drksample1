"use client";
import { type AreaRentData } from "@/lib/definitions";

type Props = {
  data: AreaRentData | null;
  loading: boolean;
};

function SkeletonRow() {
  return <div className="h-4 bg-dalock-surface rounded animate-pulse mb-2" />;
}

function RentTable({
  title,
  cols,
  rows,
}: {
  title: string;
  cols: string[];
  rows: (string | null)[][];
}) {
  return (
    <div>
      <p className="text-xs font-medium text-dalock-text1 mb-1">{title}</p>
      <div className="max-h-36 overflow-y-auto rounded-lg border border-dalock-border">
        <table className="w-full text-xs">
          <thead className="bg-dalock-surface sticky top-0">
            <tr>
              {cols.map((c, i) => (
                <th
                  key={i}
                  className={`px-2 py-1 text-dalock-text2 font-medium ${i === 0 ? "text-left" : "text-right"}`}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-t border-dalock-border">
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className={`px-2 py-1 ${j === 0 ? "text-dalock-text2" : "text-right text-dalock-text1"}`}
                  >
                    {cell ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function AreaRentPanel({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2 pt-1">
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
      </div>
    );
  }

  if (!data) return null;

  if ("error" in data) {
    return <p className="text-xs text-dalock-text2">{data.error}</p>;
  }

  if (!data.has_data) {
    return (
      <p className="text-xs text-dalock-text2">
        {data.sido ? `${data.sido} 지역 임대동향 데이터 없음` : "해당 지역 임대동향 없음"}
      </p>
    );
  }

  const fmt = (v: number | null, suffix: string) =>
    v != null ? `${v.toFixed(1)}${suffix}` : null;

  return (
    <div className="space-y-3">
      {data.quarter && (
        <p className="text-xs text-dalock-text2">{data.quarter} 기준</p>
      )}

      {data.office_areas.length > 0 && (
        <RentTable
          title="오피스 임대료"
          cols={["상권", "임대료(천원/㎡)", "공실률"]}
          rows={data.office_areas.map((a) => [
            a.name,
            fmt(a.office_rent_kwon_sqm, "천원/㎡"),
            fmt(a.office_vacancy_pct, "%"),
          ])}
        />
      )}

      {data.large_mall_areas.length > 0 && (
        <RentTable
          title="중대형상가 임대료"
          cols={["상권", "임대료(천원/㎡)", "공실률"]}
          rows={data.large_mall_areas.map((a) => [
            a.name,
            fmt(a.mall_rent_kwon_sqm, "천원/㎡"),
            fmt(a.mall_vacancy_pct, "%"),
          ])}
        />
      )}

      {data.small_mall_areas.length > 0 && (
        <RentTable
          title="소규모상가 임대료"
          cols={["상권", "임대료(천원/㎡)"]}
          rows={data.small_mall_areas.map((a) => [
            a.name,
            fmt(a.small_mall_rent_kwon_sqm, "천원/㎡"),
          ])}
        />
      )}
    </div>
  );
}
