"use client";
import { useEffect, useState } from "react";
import { type SimulationResultData } from "@/lib/definitions";
import VerdictBadge from "./VerdictBadge";

type Props = {
  result: SimulationResultData;
  onProposalClick?: () => void;
};

function formatManWon(value: number): string {
  return Math.round(value / 10_000).toLocaleString("ko-KR");
}

type MetricCardProps = { label: string; value: string; unit: string };
function MetricCard({ label, value, unit }: MetricCardProps) {
  return (
    <div className="bg-dalock-surface rounded-lg p-4 flex flex-col gap-1">
      <p className="text-xs text-dalock-text2 font-medium">{label}</p>
      <p className="text-2xl font-bold text-dalock-text1">
        {value}
        <span className="text-sm font-normal text-dalock-text2 ml-1">{unit}</span>
      </p>
    </div>
  );
}

export default function SimulationResultCard({ result, onProposalClick }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
  }, []);

  return (
    <div
      key={result.estimated_monthly_revenue}
      className={`transform transition-all duration-300 ease-out ${
        visible ? "translate-x-0 opacity-100" : "translate-x-5 opacity-0"
      } flex flex-col gap-4 p-6 h-full overflow-y-auto`}
    >
      {/* Fallback warning banner */}
      {result.fallback_used && (
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-md px-4 py-3">
          <span className="shrink-0 mt-0.5">⚠️</span>
          <span>유사 지점 데이터 부족 — 전체 평균으로 대체합니다</span>
        </div>
      )}

      {/* Verdict */}
      <div className="flex items-center gap-2">
        <VerdictBadge verdict={result.verdict} percentile={result.percentile} />
        {result.similar_branch_count > 0 && (
          <span className="text-xs text-dalock-text2">
            유사 지점 {result.similar_branch_count}개 기준
          </span>
        )}
      </div>

      {/* 3 metric cards */}
      <div className="grid grid-cols-1 gap-3">
        <MetricCard
          label="예상 월매출"
          value={formatManWon(result.estimated_monthly_revenue)}
          unit="만원"
        />
        <MetricCard
          label="점유율"
          value={result.occupancy_rate.toFixed(1)}
          unit="%"
        />
        <MetricCard
          label="예상 순수익"
          value={formatManWon(result.net_profit)}
          unit="만원"
        />
      </div>

      {/* 제안서 출력 버튼 */}
      <button
        type="button"
        onClick={onProposalClick}
        className="mt-auto w-full flex items-center justify-center rounded-md bg-dalock-primary text-white text-sm font-medium px-4 py-2.5 hover:bg-blue-700 transition-colors"
      >
        제안서 출력
      </button>
    </div>
  );
}
