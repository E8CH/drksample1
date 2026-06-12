"use client";
import { type SimulationResultData, type SimulationInput, type ComparisonEntry } from "@/lib/definitions";
import VerdictBadge from "@/components/simulation/VerdictBadge";

type Props = {
  result: SimulationResultData;
  input: SimulationInput;
};

function formatManWon(v: number) {
  return `${Math.round(v / 10_000).toLocaleString("ko-KR")}만원`;
}

function today() {
  const d = new Date();
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

function ComparisonSvgChart({
  data,
  targetRevenue,
}: {
  data: ComparisonEntry[];
  targetRevenue: number;
}) {
  const chartData = [
    { name: "분석 대상", monthly_revenue: targetRevenue, isTarget: true },
    ...data.map((d) => ({ ...d, isTarget: false })),
  ];
  const maxRev = Math.max(...chartData.map((d) => d.monthly_revenue), 1);
  const chartHeight = 100;
  const barWidth = 40;
  const gap = 14;
  const totalWidth = chartData.length * (barWidth + gap) - gap;
  const labelY = chartHeight + 18;

  return (
    <svg
      width={totalWidth}
      height={chartHeight + 28}
      viewBox={`0 0 ${totalWidth} ${chartHeight + 28}`}
      aria-label="유사 지점 월매출 비교 차트"
    >
      {chartData.map((entry, i) => {
        const barH = Math.max(2, (entry.monthly_revenue / maxRev) * chartHeight);
        const x = i * (barWidth + gap);
        const y = chartHeight - barH;
        const label = entry.name.length > 5 ? entry.name.slice(0, 5) + "…" : entry.name;
        return (
          <g key={`${entry.name}-${i}`}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={barH}
              fill={entry.isTarget ? "#2563EB" : "#BFDBFE"}
              rx={4}
            />
            <text
              x={x + barWidth / 2}
              y={labelY}
              textAnchor="middle"
              fontSize={9}
              fill="#64748B"
              fontFamily="Pretendard, sans-serif"
            >
              {label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function ProposalDocument({ result, input }: Props) {
  return (
    <div
      style={{
        width: "794px",
        backgroundColor: "#ffffff",
        fontFamily: "Pretendard, sans-serif",
        padding: "40px",
        boxSizing: "border-box",
      }}
    >
      {/* 헤더 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", borderBottom: "1px solid #E2E8F0", paddingBottom: "16px" }}>
        <div>
          <p style={{ fontSize: "12px", color: "#64748B", marginBottom: "4px" }}>🏠 다락 (Dalock)</p>
          <h1 style={{ fontSize: "20px", fontWeight: "700", color: "#0F172A", margin: 0 }}>수익분석 제안서</h1>
        </div>
        <p style={{ fontSize: "12px", color: "#64748B" }}>{today()}</p>
      </div>

      {/* 물건 정보 */}
      <div style={{ marginBottom: "20px" }}>
        <h2 style={{ fontSize: "13px", fontWeight: "600", color: "#64748B", marginBottom: "8px" }}>📋 물건 정보</h2>
        <div style={{ backgroundColor: "#F8FAFC", borderRadius: "8px", padding: "14px 16px", display: "flex", flexWrap: "wrap", gap: "16px" }}>
          {[
            { label: "주소", value: input.address },
            { label: "면적", value: `${input.areaSqm}㎡` },
            { label: "임대료", value: formatManWon(input.monthlyRent) },
            { label: "용도", value: input.buildingUse ?? "미지정" },
            { label: "EV충전", value: input.evCharging ? "가능" : "불가" },
          ].map(({ label, value }) => (
            <span key={label} style={{ fontSize: "13px", color: "#0F172A" }}>
              <span style={{ color: "#64748B" }}>{label} </span>
              {value}
            </span>
          ))}
        </div>
      </div>

      {/* 수치 도표 */}
      <div style={{ marginBottom: "20px" }}>
        <h2 style={{ fontSize: "13px", fontWeight: "600", color: "#64748B", marginBottom: "8px" }}>📊 시뮬레이션 결과</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
          {[
            { label: "예상 월매출", value: formatManWon(result.estimated_monthly_revenue), danger: false },
            { label: "예상 점유율", value: `${result.occupancy_rate.toFixed(1)}%`, danger: false },
            { label: "예상 순수익", value: formatManWon(result.net_profit), danger: result.net_profit < 0 },
          ].map(({ label, value, danger }) => (
            <div key={label} style={{ backgroundColor: "#F8FAFC", borderRadius: "8px", padding: "16px", textAlign: "center" }}>
              <p style={{ fontSize: "11px", color: "#64748B", marginBottom: "4px" }}>{label}</p>
              <p style={{ fontSize: "18px", fontWeight: "700", color: danger ? "#EF4444" : "#0F172A", margin: 0 }}>{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 비교 차트 */}
      {result.comparison_data.length > 0 && (
        <div style={{ marginBottom: "20px" }}>
          <h2 style={{ fontSize: "13px", fontWeight: "600", color: "#64748B", marginBottom: "8px" }}>📈 브랜드 내 유사 지점 비교</h2>
          {result.fallback_used && (
            <p style={{ fontSize: "11px", color: "#F59E0B", marginBottom: "6px" }}>
              ⚠️ 인근 유사 지점 데이터가 부족하여 전국 기준으로 비교합니다.
            </p>
          )}
          <div style={{ display: "flex", justifyContent: "center" }}>
            <ComparisonSvgChart
              data={result.comparison_data}
              targetRevenue={result.estimated_monthly_revenue}
            />
          </div>
          <p style={{ fontSize: "11px", color: "#64748B", textAlign: "center", marginTop: "6px" }}>
            <span style={{ display: "inline-block", width: "12px", height: "12px", borderRadius: "2px", backgroundColor: "#2563EB", marginRight: "4px", verticalAlign: "middle" }} />
            분석 대상
            <span style={{ display: "inline-block", width: "12px", height: "12px", borderRadius: "2px", backgroundColor: "#BFDBFE", marginLeft: "12px", marginRight: "4px", verticalAlign: "middle" }} />
            유사 지점
          </p>
        </div>
      )}

      {/* 종합 판정 */}
      <div style={{ borderTop: "1px solid #E2E8F0", paddingTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
        <VerdictBadge verdict={result.verdict} percentile={result.percentile} />
        {result.similar_branch_count > 0 && (
          <span style={{ fontSize: "11px", color: "#64748B" }}>유사 지점 {result.similar_branch_count}개 기준</span>
        )}
      </div>
    </div>
  );
}
