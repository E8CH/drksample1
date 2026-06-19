"use client";
import { type RentData } from "@/lib/definitions";

type Props = {
  data: RentData | null;
  loading: boolean;
};

function SkeletonRow() {
  return <div className="h-4 bg-dalock-surface rounded animate-pulse mb-2" />;
}

export default function RentInfoPanel({ data, loading }: Props) {
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

  if (data.transactions.length === 0) {
    return <p className="text-xs text-dalock-text2">최근 2년 실거래 내역이 없습니다</p>;
  }

  return (
    <div className="max-h-52 overflow-y-auto rounded-lg border border-dalock-border">
      <table className="w-full text-xs">
        <thead className="bg-dalock-surface sticky top-0">
          <tr>
            <th className="text-left px-2 py-1.5 text-dalock-text2 font-medium">거래일</th>
            <th className="text-left px-2 py-1.5 text-dalock-text2 font-medium">층/㎡</th>
            <th className="text-right px-2 py-1.5 text-dalock-text2 font-medium">금액</th>
          </tr>
        </thead>
        <tbody>
          {data.transactions.map((t, i) => (
            <tr key={i} className="border-t border-dalock-border hover:bg-dalock-surface/50">
              <td className="px-2 py-1.5 text-dalock-text2">{t.date}</td>
              <td className="px-2 py-1.5 text-dalock-text2">
                {t.floor ? `${t.floor}층` : ""}
                {t.area_sqm > 0 && (
                  <span className="ml-1">{t.area_sqm.toFixed(1)}㎡</span>
                )}
              </td>
              <td className="px-2 py-1.5 text-right font-semibold text-dalock-text1">
                {t.amount_wan > 0
                  ? `${t.amount_wan.toLocaleString("ko-KR")}만`
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
