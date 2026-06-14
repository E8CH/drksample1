"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { generateData, checkGenerationStatus, deleteAllData } from "@/actions/data";

type Props = {
  initialYear?: string;
  initialBranchName?: string;
};

const DATA_START_YEAR = 2016;
const currentYear = new Date().getFullYear();
const YEARS = Array.from(
  { length: currentYear - DATA_START_YEAR + 1 },
  (_, i) => String(currentYear - i)
);

export default function TableToolbar({ initialYear, initialBranchName }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [branchInput, setBranchInput] = useState(initialBranchName ?? "");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // 폴링: isGenerating 동안 2초마다 /data/status 체크
  useEffect(() => {
    if (!isGenerating) return;
    pollingRef.current = setInterval(async () => {
      const { status } = await checkGenerationStatus();
      if (status === "idle") {
        clearInterval(pollingRef.current!);
        pollingRef.current = null;
        setIsGenerating(false);
        toast.success("데이터 재생성이 완료되었습니다", { duration: 3000 });
        router.refresh();
      }
    }, 2000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [isGenerating, router]);

  function buildParams(overrides: Record<string, string | null>) {
    const p = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(overrides)) {
      if (v === null || v === "") p.delete(k);
      else p.set(k, v);
    }
    p.set("page", "1");
    return p.toString();
  }

  function handleYearChange(value: string) {
    router.push(`?${buildParams({ year: value === "all" ? null : value })}`);
  }

  function handleSearch() {
    router.push(`?${buildParams({ branch_name: branchInput.trim() || null })}`);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSearch();
  }

  async function handleConfirmGenerate() {
    setIsDialogOpen(false);
    const result = await generateData();
    if (!result.success) {
      toast.error(
        result.error === "already_running"
          ? "이미 재생성이 진행 중입니다"
          : "재생성 요청에 실패했습니다"
      );
      return;
    }
    setIsGenerating(true);
  }

  async function handleConfirmDelete() {
    setIsDeleteDialogOpen(false);
    setIsDeleting(true);
    const result = await deleteAllData();
    setIsDeleting(false);
    if (!result.success) {
      toast.error("삭제 요청에 실패했습니다");
      return;
    }
    toast.success("전체 데이터가 삭제되었습니다", { duration: 3000 });
    router.refresh();
  }

  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* 연도 필터 */}
      <Select
        defaultValue={initialYear ?? "all"}
        onValueChange={handleYearChange}
      >
        <SelectTrigger className="w-[120px]" aria-label="연도 필터">
          <SelectValue placeholder="연도" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">전체</SelectItem>
          {YEARS.map((y) => (
            <SelectItem key={y} value={y}>
              {y}년
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 지점명 검색 */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={branchInput}
          onChange={(e) => setBranchInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="지점명 검색"
          className="h-9 px-3 text-sm rounded-md border border-dalock-border bg-white text-dalock-text1 placeholder:text-dalock-text2 focus:outline-none focus:ring-2 focus:ring-dalock-primary focus:border-transparent transition"
          aria-label="지점명 검색"
        />
        <button
          onClick={handleSearch}
          className="h-9 px-4 text-sm rounded-md bg-dalock-surface border border-dalock-border text-dalock-text1 hover:bg-dalock-border transition-colors"
          aria-label="검색"
        >
          검색
        </button>
      </div>

      {/* 전체 재생성 버튼 — ml-auto로 우측 배치 */}
      <button
        onClick={() => setIsDialogOpen(true)}
        disabled={isGenerating || isDeleting}
        className="h-9 px-4 text-sm rounded-md bg-dalock-primary text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ml-auto"
        aria-label="전체 재생성"
        aria-busy={isGenerating}
      >
        {isGenerating ? "재생성 중..." : "전체 재생성"}
      </button>

      {/* 전체 삭제 버튼 */}
      <button
        onClick={() => setIsDeleteDialogOpen(true)}
        disabled={isGenerating || isDeleting}
        className="h-9 px-4 text-sm rounded-md bg-white border border-red-400 text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        aria-label="전체 삭제"
      >
        {isDeleting ? "삭제 중..." : "전체 삭제"}
      </button>

      {/* 재생성 확인 Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="w-[400px] p-6">
          <h2 className="text-lg font-semibold text-dalock-text1 mb-2">
            전체 데이터 재생성
          </h2>
          <p className="text-sm text-dalock-text2 mb-6">
            정말 전체 데이터를 재생성하시겠습니까?
            <br />
            기존 데이터가 모두 삭제되고 새 데이터로 대체됩니다.
          </p>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsDialogOpen(false)}
              className="h-9 px-4 text-sm rounded-md border border-dalock-border text-dalock-text1 hover:bg-dalock-surface transition-colors"
            >
              취소
            </button>
            <button
              onClick={handleConfirmGenerate}
              className="h-9 px-4 text-sm rounded-md bg-dalock-primary text-white hover:bg-blue-700 transition-colors"
            >
              확인
            </button>
          </div>
        </DialogContent>
      </Dialog>

      {/* 삭제 확인 Dialog — ESC/배경클릭 차단 (파괴적 액션) */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent
          onInteractOutside={(e) => e.preventDefault()}
          onEscapeKeyDown={(e) => e.preventDefault()}
          className="w-[400px] p-6"
        >
          <h2 className="text-lg font-semibold text-dalock-text1 mb-2">
            전체 데이터 삭제
          </h2>
          <p className="text-sm text-dalock-text2 mb-6">
            이 작업은 되돌릴 수 없습니다. 정말 삭제하시겠습니까?
            <br />
            sales, operations, members 데이터가 모두 삭제됩니다.
          </p>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsDeleteDialogOpen(false)}
              className="h-9 px-4 text-sm rounded-md border border-dalock-border text-dalock-text1 hover:bg-dalock-surface transition-colors"
            >
              취소
            </button>
            <button
              onClick={handleConfirmDelete}
              className="h-9 px-4 text-sm rounded-md bg-red-600 text-white hover:bg-red-700 transition-colors"
            >
              삭제
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
