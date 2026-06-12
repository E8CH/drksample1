"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

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
    </div>
  );
}
