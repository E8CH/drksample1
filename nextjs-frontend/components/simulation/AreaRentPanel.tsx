"use client";
import { type AreaRentData } from "@/lib/definitions";

type Props = {
  data: AreaRentData | null;
  loading: boolean;
};

function SkeletonRow() {
  return <div className="h-4 bg-dalock-surface rounded animate-pulse mb-2" />;
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

  return (
    <div className="space-y-3">
      {data.quarter && (
        <p className="text-xs text-dalock-text2">{data.quarter} 기준</p>
      )}

      {data.office_areas.length > 0 && (
        <div>
          <p className="text-xs font-medium text-dalock-text1 mb-1">오피스 임대료</p>
          <div className="max-h-36 overflow-y-auto rounded-lg border border-dalock-border">
            <table className="w-full text-xs">
              <thead className="bg-dalock-surface sticky top-0">
                <tr>
                  <th className="text-left px-2 py-1 text-dalock-text2 font-medium">상권</th>
                  <th className="text-right px-2 py-1 text-dalock-text2 font-medium">임대료</th>
                  <th className="text-right px-2 py-1 text-dalock-text2 font-medium">공실률</th>
                </tr>
              </thead>
              <tbody>
                {data.office_areas.map((a, i) => (
                  <tr key={i} className="border-t border-dalock-border">
                    <td className="px-2 py-1 text-dalock-text2">{a.name}</td>
                    <td className="px-2 py-1 text-right text-dalock-text1">
                      {a.office_rent_kwon_sqm != null
                        ? `${a.office_rent_kwon_sqm.toFixed(1)}천원/㎡`
                        : "—"}
                    </td>
                    <td className="px-2 py-1 text-right text-dalock-text2">
                      {a.office_vacancy_pct != null
                        ? `${a.office_vacancy_pct.toFixed(1)}%`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data.mall_areas.length > 0 && (
        <div>
          <p className="text-xs font-medium text-dalock-text1 mb-1">중대형상가 임대료</p>
          <div className="max-h-36 overflow-y-auto rounded-lg border border-dalock-border">
            <table className="w-full text-xs">
              <thead className="bg-dalock-surface sticky top-0">
                <tr>
                  <th className="text-left px-2 py-1 text-dalock-text2 font-medium">상권</th>
                  <th className="text-right px-2 py-1 text-dalock-text2 font-medium">임대료</th>
                </tr>
              </thead>
              <tbody>
                {data.mall_areas.map((a, i) => (
                  <tr key={i} className="border-t border-dalock-border">
                    <td className="px-2 py-1 text-dalock-text2">{a.name}</td>
                    <td className="px-2 py-1 text-right text-dalock-text1">
                      {a.mall_rent_kwon_sqm != null
                        ? `${a.mall_rent_kwon_sqm.toFixed(1)}천원/㎡`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
