"use client";
import { useRef, useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import {
  type SimulationResultData,
  type SimulationInput,
} from "@/lib/definitions";
import VerdictBadge from "@/components/simulation/VerdictBadge";
import ComparisonBarChart from "@/components/simulation/ComparisonBarChart";
import ProposalDocument from "./ProposalDocument";
import { downloadProposalPDF, generatePdfFilename } from "@/lib/pdf";

type Props = {
  open: boolean;
  onClose: () => void;
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

export default function ProposalModal({ open, onClose, result, input }: Props) {
  const docRef = useRef<HTMLDivElement>(null);
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    if (!docRef.current) return;
    setDownloading(true);
    try {
      const filename = generatePdfFilename(input.address);
      await downloadProposalPDF(docRef.current, filename);
    } catch {
      alert("PDF 저장 중 오류가 발생했습니다. 다시 시도해 주세요.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <>
      {/* 오프스크린 ProposalDocument — html2canvas 캡처 타겟 */}
      <div
        ref={docRef}
        aria-hidden="true"
        style={{ position: "fixed", top: 0, left: "-9999px", width: "794px", zIndex: -1 }}
      >
        <ProposalDocument result={result} input={input} />
      </div>

      <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent
        className="max-w-[680px] w-[90vw] max-h-[90vh] overflow-y-auto flex flex-col gap-0 p-0"
        onInteractOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-dalock-border">
          <div>
            <p className="text-xs text-dalock-text2">🏠 다락 (Dalock)</p>
            <h2 className="text-lg font-semibold text-dalock-text1">수익분석 제안서</h2>
          </div>
          <button
            onClick={onClose}
            aria-label="닫기"
            className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-md hover:bg-dalock-surface text-dalock-text2 hover:text-dalock-text1 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* 본문 */}
        <div className="px-6 py-5 flex flex-col gap-5">
          {/* 물건 정보 */}
          <section>
            <h3 className="text-sm font-semibold text-dalock-text2 mb-2">📋 물건 정보</h3>
            <div className="bg-dalock-surface rounded-lg p-4 flex flex-wrap gap-x-6 gap-y-1 text-sm text-dalock-text1">
              <span>
                <span className="text-dalock-text2">주소 </span>
                {input.address}
              </span>
              <span>
                <span className="text-dalock-text2">면적 </span>
                {input.areaSqm}㎡
              </span>
              <span>
                <span className="text-dalock-text2">임대료 </span>
                {formatManWon(input.monthlyRent)}
              </span>
              <span>
                <span className="text-dalock-text2">용도 </span>
                {input.buildingUse ?? "미지정"}
              </span>
              <span>
                <span className="text-dalock-text2">EV충전 </span>
                {input.evCharging ? "가능" : "불가"}
              </span>
            </div>
          </section>

          {/* 수치 도표 */}
          <section>
            <h3 className="text-sm font-semibold text-dalock-text2 mb-2">📊 시뮬레이션 결과</h3>
            <div className="grid grid-cols-3 gap-3">
              {(
                [
                  {
                    label: "예상 월매출",
                    value: formatManWon(result.estimated_monthly_revenue),
                    danger: false,
                  },
                  {
                    label: "예상 점유율",
                    value: `${result.occupancy_rate.toFixed(1)}%`,
                    danger: false,
                  },
                  {
                    label: "예상 순수익",
                    value: formatManWon(result.net_profit),
                    danger: result.net_profit < 0,
                  },
                ] as const
              ).map(({ label, value, danger }) => (
                <div
                  key={label}
                  className="bg-dalock-surface rounded-lg p-4 text-center"
                >
                  <p className="text-xs text-dalock-text2 mb-1">{label}</p>
                  <p
                    className={`text-xl font-bold ${
                      danger ? "text-dalock-danger" : "text-dalock-text1"
                    }`}
                  >
                    {value}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* 비교 차트 */}
          {result.comparison_data.length > 0 && (
            <section aria-label="유사 지점 월매출 비교 차트">
              <h3 className="text-sm font-semibold text-dalock-text2 mb-2">
                📈 브랜드 내 유사 지점 비교
              </h3>
              <ComparisonBarChart
                data={result.comparison_data}
                targetRevenue={result.estimated_monthly_revenue}
              />
              <p className="text-xs text-dalock-text2 mt-1 text-center">
                <span className="inline-block w-3 h-3 rounded-sm bg-[#2563EB] mr-1 align-middle" />
                분석 대상
                <span className="inline-block w-3 h-3 rounded-sm bg-[#BFDBFE] ml-3 mr-1 align-middle" />
                유사 지점
              </p>
            </section>
          )}

          {/* 판정 배지 */}
          <section className="flex items-center gap-3">
            <VerdictBadge verdict={result.verdict} percentile={result.percentile} />
            {result.similar_branch_count > 0 && (
              <span className="text-xs text-dalock-text2">
                유사 지점 {result.similar_branch_count}개 기준
              </span>
            )}
          </section>
        </div>

        {/* 하단 */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-dalock-border">
          <span className="text-xs text-dalock-text2">{today()}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              disabled={downloading}
              aria-busy={downloading}
              className="px-4 py-2 text-sm rounded-md bg-dalock-primary text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {downloading ? "저장 중..." : "PDF 저장"}
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-md border border-dalock-border text-dalock-text1 hover:bg-dalock-surface transition-colors"
            >
              닫기
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
    </>
  );
}
