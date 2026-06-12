"use client";

import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from "@tanstack/react-table";
import { useRouter, useSearchParams } from "next/navigation";
import { type SalesRow } from "@/lib/definitions";

type Props = {
  data: SalesRow[];
  total: number;
  page: number;
  limit: number;
  sortBy: string;
  order: "asc" | "desc";
};

function formatManWon(v: number): string {
  return `${Math.round(v / 10_000).toLocaleString("ko-KR")}만원`;
}

function formatMonth(s: string): string {
  const [year, month] = s.split("-");
  return `${year}년 ${month}월`;
}

const SORTABLE_COLUMNS: Record<string, string> = {
  branch_name: "branch_name",
  sale_month: "sale_date",
  monthly_revenue: "monthly_revenue",
  net_profit: "net_profit",
  occupancy_rate: "occupancy_rate",
};

export default function BranchDataTable({
  data,
  total,
  page,
  limit,
  sortBy,
  order,
}: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const totalPages = Math.ceil(total / limit);

  function buildParams(overrides: Record<string, string | null>) {
    const p = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(overrides)) {
      if (v === null) p.delete(k);
      else p.set(k, v);
    }
    return p.toString();
  }

  function handleSort(colKey: string) {
    const apiKey = SORTABLE_COLUMNS[colKey];
    if (!apiKey) return;
    const nextOrder = sortBy === apiKey && order === "asc" ? "desc" : "asc";
    router.push(`?${buildParams({ sort_by: apiKey, order: nextOrder, page: "1" })}`);
  }

  function handlePage(next: number) {
    router.push(`?${buildParams({ page: String(next) })}`);
  }

  const columns: ColumnDef<SalesRow>[] = [
    {
      accessorKey: "branch_name",
      header: "지점명",
      cell: (info) => (
        <span className="font-medium text-dalock-text1">{info.getValue<string>()}</span>
      ),
    },
    {
      accessorKey: "address",
      header: "주소",
      cell: (info) => (
        <span
          className="block max-w-[160px] truncate text-dalock-text2 text-sm"
          title={info.getValue<string>()}
        >
          {info.getValue<string>()}
        </span>
      ),
    },
    {
      accessorKey: "sale_month",
      header: "기준연월",
      cell: (info) => formatMonth(info.getValue<string>()),
    },
    {
      accessorKey: "monthly_revenue",
      header: "월매출",
      cell: (info) => formatManWon(info.getValue<number>()),
    },
    {
      accessorKey: "electricity_fee",
      header: "전기세",
      cell: (info) => formatManWon(info.getValue<number>()),
    },
    {
      accessorKey: "operating_cost",
      header: "운영비",
      cell: (info) => formatManWon(info.getValue<number>()),
    },
    {
      accessorKey: "net_profit",
      header: "순수익",
      cell: (info) => {
        const v = info.getValue<number>();
        return (
          <span className={v < 0 ? "text-dalock-danger font-medium" : ""}>
            {formatManWon(v)}
          </span>
        );
      },
    },
    {
      accessorKey: "occupancy_rate",
      header: "점유율",
      cell: (info) => `${info.getValue<number>().toFixed(1)}%`,
    },
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    manualPagination: true,
    pageCount: totalPages,
  });

  function SortIcon({ colKey }: { colKey: string }) {
    const apiKey = SORTABLE_COLUMNS[colKey];
    if (!apiKey) return null;
    if (sortBy !== apiKey) return <span className="ml-1 text-dalock-text2 opacity-40">↕</span>;
    return (
      <span className="ml-1 text-dalock-primary">
        {order === "asc" ? "↑" : "↓"}
      </span>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {/* 총 건수 */}
      <p className="text-xs text-dalock-text2">총 {total.toLocaleString("ko-KR")}건</p>

      {/* 테이블 */}
      <div className="overflow-x-auto rounded-lg border border-dalock-border">
        <table className="w-full text-sm text-left border-collapse">
          <thead className="bg-dalock-surface text-dalock-text2">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const colKey = header.id;
                  const sortable = colKey in SORTABLE_COLUMNS;
                  return (
                    <th
                      key={header.id}
                      className={`px-4 py-3 font-medium whitespace-nowrap border-b border-dalock-border ${
                        sortable ? "cursor-pointer select-none hover:text-dalock-text1" : ""
                      }`}
                      onClick={sortable ? () => handleSort(colKey) : undefined}
                      aria-sort={
                        sortBy === SORTABLE_COLUMNS[colKey]
                          ? order === "asc"
                            ? "ascending"
                            : "descending"
                          : sortable
                          ? "none"
                          : undefined
                      }
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {sortable && <SortIcon colKey={colKey} />}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-16 text-center text-dalock-text2"
                >
                  데이터가 없습니다
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-dalock-border hover:bg-dalock-surface/50 transition-colors"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-dalock-text1 whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-dalock-text2">
          <span>
            {page} / {totalPages} 페이지
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePage(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-md border border-dalock-border hover:bg-dalock-surface disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="이전 페이지"
            >
              이전
            </button>
            <button
              onClick={() => handlePage(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-md border border-dalock-border hover:bg-dalock-surface disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="다음 페이지"
            >
              다음
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
