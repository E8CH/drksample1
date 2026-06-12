# Story 3.3: PDF 다운로드

Status: review

## Story

As a 관리자,
I want 제안서 팝업에서 "PDF 저장" 버튼을 클릭하여 제안서를 PDF 파일로 다운로드하고 싶다,
So that 이 파일을 제안 자료로 즉시 활용할 수 있다.

## Acceptance Criteria

1. **Given** ProposalModal이 열린 상태 **When** "PDF 저장" 버튼 클릭 **Then** 파일명 `수익분석제안서_{주소}_{날짜}.pdf` 형식으로 PDF 다운로드됨 (AC1 — FR-5)

2. **Given** PDF 생성 중 **When** html2canvas + jsPDF 실행 **Then** ProposalDocument(순수 CSS/SVG 차트) 영역이 캡처되어 A4 비율 PDF로 출력됨. Recharts SVG를 직접 캡처하지 않음 (AC2 — ARCH-7)

3. **Given** 생성된 PDF 파일 **When** PDF 뷰어에서 열람 **Then** 브랜드 로고(텍스트), 물건 정보, 수치 도표, 비교 차트, 판정 배지, 날짜가 레이아웃 깨짐 없이 표시됨 (AC3)

4. **Given** Pretendard 폰트 사용 **When** PDF 캡처 **Then** 한글 텍스트가 깨지지 않고 정상 렌더링됨 (AC4 — html2canvas + 폰트 로드 대기)

5. **Given** PDF 저장 버튼 클릭 **When** 생성 중 **Then** 버튼이 비활성화되고 로딩 텍스트("저장 중...")가 표시됨. 완료 후 다시 활성화됨 (AC5 — UX-DR14)

## Tasks / Subtasks

- [x] Task 1: 패키지 설치
  - [x] `cd nextjs-frontend && npm install html2canvas jspdf`
  - [x] html2canvas v1.4.x + jspdf v2.5.x 설치 확인 (둘 다 TypeScript 타입 내장)

- [x] Task 2: PDF 생성 유틸리티 (lib/pdf.ts)
  - [x] `nextjs-frontend/lib/pdf.ts` 신규 생성
  - [x] `downloadProposalPDF(element: HTMLElement, filename: string): Promise<void>` 함수
  - [x] html2canvas `{ scale: 2, useCORS: true, logging: false }` 옵션
  - [x] jsPDF `{ orientation: "portrait", unit: "mm", format: "a4" }` 설정
  - [x] canvas → A4 전체 너비로 이미지 삽입 (`pdfWidth = pdf.internal.pageSize.getWidth()`)
  - [x] `sanitizeFilename(address: string): string` 함수 — `[\\/:*?"<>|]` → `_`, 50자 제한
  - [x] `generatePdfFilename(address: string): string` 함수 — `수익분석제안서_{주소}_{YYYY-MM-DD}.pdf`

- [x] Task 3: ProposalDocument 컴포넌트 신규 생성 (PDF 캡처 전용)
  - [x] `nextjs-frontend/components/proposal/ProposalDocument.tsx` 신규 생성 (`"use client"`)
  - [x] Props: `result: SimulationResultData`, `input: SimulationInput`
  - [x] 고정 너비 794px (A4 96dpi 기준), 배경 흰색, Pretendard 폰트
  - [x] 헤더: "🏠 다락 (Dalock)" + "수익분석 제안서" + 날짜
  - [x] 물건 정보 섹션 (ProposalModal과 동일 데이터, 같은 포맷)
  - [x] 수치 도표: 3열 grid (예상 월매출/점유율/순수익 카드)
  - [x] 순수 SVG 바 차트 — Recharts 금지, `ComparisonSvgChart` 인라인 서브컴포넌트
  - [x] 판정 배지 (인라인 span, VerdictBadge import 가능)
  - [x] `comparison_data.length === 0` 시 SVG 차트 섹션 숨김
  - [x] `fallback_used === true` 시 경고 텍스트 표시

- [x] Task 4: ProposalModal에 PDF 저장 버튼 추가
  - [x] `nextjs-frontend/components/proposal/ProposalModal.tsx` 수정
  - [x] `useRef<HTMLDivElement>(null)` (docRef) 추가
  - [x] `useState<boolean>(false)` (downloading) 추가
  - [x] 모달 JSX 외부에 오프스크린 컨테이너 추가:
    ```tsx
    <div ref={docRef} style={{ position: "fixed", top: 0, left: "-9999px", width: "794px", zIndex: -1 }}>
      {open && <ProposalDocument result={result} input={input} />}
    </div>
    ```
  - [x] `handleDownload()` 함수: `await document.fonts.ready` → `downloadProposalPDF(docRef.current, filename)`
  - [x] 하단 "닫기" 버튼 왼쪽에 "PDF 저장" 버튼 추가 (Primary 스타일)
  - [x] downloading 중 버튼 `disabled` + "저장 중..." 텍스트 (스피너 선택)
  - [x] try/finally로 downloading 상태 항상 해제

- [x] Task 5: TypeScript 타입 검사 및 검증
  - [x] `cd nextjs-frontend && npx tsc --noEmit` — 오류 없음

## Dev Notes

### 현재 상태 (Story 3-2 이후)

**ProposalModal.tsx 현재 상태:**
```tsx
// 하단 버튼 영역 (현재)
<div className="flex items-center justify-between px-6 py-4 border-t border-dalock-border">
  <span className="text-xs text-dalock-text2">{today()}</span>
  <button onClick={onClose} className="px-4 py-2 text-sm rounded-md border border-dalock-border ...">
    닫기
  </button>
</div>
```
→ 이 하단에 "PDF 저장" 버튼을 `닫기` 버튼 오른쪽(또는 왼쪽)에 추가.

**ProposalModal Props (현재):**
```tsx
type Props = {
  open: boolean;
  onClose: () => void;
  result: SimulationResultData;
  input: SimulationInput;
};
```
→ Props 변경 없음. `useRef`, `useState`만 추가.

### ARCH-7 핵심 제약: html2canvas + Recharts 충돌

**절대 금지**: ProposalModal 내의 Recharts `<ComparisonBarChart>`를 html2canvas로 직접 캡처하지 말 것.

**이유**: html2canvas는 `foreignObject` 내 HTML 요소를 완전히 렌더링하지 못하며, Recharts는 SVG 내에 `<foreignObject>`를 사용할 수 있음. 결과적으로 캡처 시 차트가 빈칸으로 출력될 수 있음.

**해결책**: `ProposalDocument.tsx`에 순수 SVG 바 차트를 별도 구현.

### ProposalDocument 레이아웃 설계

```
┌─────────────────────────────────────────────┐ (794px)
│ 🏠 다락 (Dalock)         수익분석 제안서      │
│                                  2026.06.13  │
├─────────────────────────────────────────────┤
│ 📋 물건 정보                                  │
│ [bg-gray-50 rounded] 주소|면적|임대료|용도|EV │
├─────────────────────────────────────────────┤
│ 📊 시뮬레이션 결과                            │
│ [월매출 카드] [점유율 카드] [순수익 카드]       │
├─────────────────────────────────────────────┤
│ 📈 유사 지점 비교 (comparison_data.length > 0) │
│ [순수 SVG 바 차트]                           │
├─────────────────────────────────────────────┤
│ 종합 판정: [추천/검토필요/비추천 뱃지]         │
└─────────────────────────────────────────────┘
```

### 순수 SVG 바 차트 구현 패턴

```tsx
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
          <g key={entry.name}>
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
```

### pdf.ts 유틸리티 패턴

```typescript
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

export function sanitizeFilename(address: string): string {
  return address.replace(/[\\/:*?"<>|]/g, "_").replace(/\s+/g, "_").slice(0, 50);
}

export function generatePdfFilename(address: string): string {
  const d = new Date();
  const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  return `수익분석제안서_${sanitizeFilename(address)}_${dateStr}.pdf`;
}

export async function downloadProposalPDF(
  element: HTMLElement,
  filename: string
): Promise<void> {
  await document.fonts.ready;
  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    logging: false,
    backgroundColor: "#ffffff",
  });
  const imgData = canvas.toDataURL("image/png");
  const pdf = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });
  const pdfWidth = pdf.internal.pageSize.getWidth();
  const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
  pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
  pdf.save(filename);
}
```

### ProposalModal 수정 패턴

```tsx
import { useRef, useState } from "react";
import ProposalDocument from "./ProposalDocument";
import { downloadProposalPDF, generatePdfFilename } from "@/lib/pdf";

export default function ProposalModal({ open, onClose, result, input }: Props) {
  const docRef = useRef<HTMLDivElement>(null);
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    if (!docRef.current) return;
    setDownloading(true);
    try {
      const filename = generatePdfFilename(input.address);
      await downloadProposalPDF(docRef.current, filename);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <>
      {/* 오프스크린 ProposalDocument — html2canvas 캡처 타겟 */}
      <div
        ref={docRef}
        style={{ position: "fixed", top: 0, left: "-9999px", width: "794px", zIndex: -1 }}
      >
        {open && <ProposalDocument result={result} input={input} />}
      </div>

      <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
        <DialogContent ...>
          {/* ... 기존 내용 유지 ... */}
          
          {/* 하단 — 날짜 + 버튼 그룹 */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-dalock-border">
            <span className="text-xs text-dalock-text2">{today()}</span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleDownload}
                disabled={downloading}
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
```

### 파일 위치

| 파일 | 상태 | 비고 |
|------|------|------|
| `nextjs-frontend/lib/pdf.ts` | 신규 | html2canvas + jsPDF 유틸리티 |
| `nextjs-frontend/components/proposal/ProposalDocument.tsx` | 신규 | PDF 캡처 전용, Recharts 금지 |
| `nextjs-frontend/components/proposal/ProposalModal.tsx` | 수정 | PDF 저장 버튼 + docRef + downloading |

### NFR 준수

- **NFR-2**: PDF 생성은 클라이언트 사이드 (html2canvas + jsPDF). API 키 미사용 — OK.
- **NFR-7 WCAG AA**: "PDF 저장" 버튼에 `disabled` 상태 + `aria-busy` 속성 권장.
- **ARCH-7**: ProposalDocument는 순수 CSS/SVG 차트 — Recharts 미사용. 이것이 이 스토리의 핵심 아키텍처 제약.

### html2canvas v1.4 주의 사항

- `background-color: transparent` → `backgroundColor: "#ffffff"` 옵션으로 흰 배경 강제
- `position: fixed; left: -9999px` 컨테이너: html2canvas가 뷰포트 밖 요소를 캡처하려면 `scrollX`/`scrollY` 보정이 필요할 수 있음. 문제 발생 시 `windowWidth: element.scrollWidth` 옵션 추가.
- **한글 폰트**: `document.fonts.ready` await로 Pretendard 완전 로드 후 캡처. CDN 폰트라면 `useCORS: true` 필요.

### 이전 스토리 학습 (Story 3-2)

- `"use client"` 필수 — 모든 클라이언트 컴포넌트에 선언
- `formatManWon` 유틸 함수는 ProposalModal에 이미 정의됨 → ProposalDocument에 재정의 또는 공유 유틸로 이동
- `today()` 함수도 ProposalModal에 이미 정의됨 → 동일 패턴 재사용
- `SimulationResultData`, `SimulationInput`, `ComparisonEntry` 타입은 `@/lib/definitions`에서 임포트
- Tooltip 등 Recharts 특화 컴포넌트는 ProposalDocument에서 완전 제외

## Dev Agent Record

### Implementation Plan

1. html2canvas + jspdf 패키지 설치
2. `lib/pdf.ts` 유틸리티 구현 (sanitizeFilename, generatePdfFilename, downloadProposalPDF)
3. `ProposalDocument.tsx` 신규 생성 — 순수 CSS/SVG 레이아웃 + ComparisonSvgChart
4. `ProposalModal.tsx` 수정 — docRef + downloading state + handleDownload + PDF 저장 버튼
5. tsc --noEmit 검증

### Debug Log

_(구현 중 추가)_

### Completion Notes

- html2canvas v1.4.1 + jsPDF v4.2.1 설치 (jsPDF v4는 default export 유지, API 호환)
- `lib/pdf.ts`: sanitizeFilename / generatePdfFilename / downloadProposalPDF 구현. `document.fonts.ready` await로 Pretendard 완전 로드 후 캡처. scale:2, backgroundColor:"#ffffff"
- `ProposalDocument.tsx`: 794px 고정 너비, 인라인 스타일 사용(Tailwind 클래스 대신 off-screen 렌더링 안정성 확보). ComparisonSvgChart 인라인 SVG 구현 — Recharts 완전 배제(ARCH-7 준수)
- `ProposalModal.tsx`: docRef(off-screen 컨테이너) + downloading state + handleDownload(try/finally). PDF 저장 버튼: aria-busy, disabled, "저장 중..." 로딩 텍스트(AC5/UX-DR14)
- `npx tsc --noEmit` — 오류 없음

## File List

**신규 생성:**
- `nextjs-frontend/lib/pdf.ts`
- `nextjs-frontend/components/proposal/ProposalDocument.tsx`

**수정:**
- `nextjs-frontend/components/proposal/ProposalModal.tsx`

## Change Log

- 2026-06-13: Story 3-3 CS 생성. html2canvas + jsPDF 클라이언트 사이드 PDF. ProposalDocument(순수 SVG 차트)로 Recharts 캡처 충돌 방지. ProposalModal에 PDF 저장 버튼 추가.
- 2026-06-13: Story 3-3 DS 완료. lib/pdf.ts, ProposalDocument.tsx 신규 생성. ProposalModal.tsx PDF 저장 버튼 추가. tsc --noEmit 통과. Status → review.
