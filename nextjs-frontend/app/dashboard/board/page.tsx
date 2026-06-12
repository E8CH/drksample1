import { Suspense } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import BranchDataTable from "@/components/board/BranchDataTable";
import TableToolbar from "@/components/board/TableToolbar";
import { type SalesListResponse } from "@/lib/definitions";

type SearchParams = {
  sort_by?: string;
  order?: string;
  page?: string;
  year?: string;
  branch_name?: string;
};

async function fetchSales(params: SearchParams): Promise<SalesListResponse> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) redirect("/login");

  const url = new URL(`${process.env.API_URL}/sales`);
  if (params.sort_by) url.searchParams.set("sort_by", params.sort_by);
  if (params.order) url.searchParams.set("order", params.order);
  if (params.page) url.searchParams.set("page", params.page);
  if (params.year) url.searchParams.set("year", params.year);
  if (params.branch_name) url.searchParams.set("branch_name", params.branch_name);

  const res = await fetch(url.toString(), {
    headers: { Cookie: `access_token=${token}` },
    cache: "no-store",
  });

  if (res.status === 401) redirect("/login");
  if (!res.ok) throw new Error(`GET /sales failed: ${res.status}`);
  return res.json();
}

function TableSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-10 bg-dalock-surface rounded-md mb-2" />
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="h-12 bg-dalock-surface rounded-md mb-1 opacity-70" />
      ))}
    </div>
  );
}

export default async function BoardPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  const salesData = await fetchSales(params);

  return (
    <div className="p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-dalock-text1">수익분석표 게시판</h1>
      </div>
      <Suspense fallback={<div className="h-9 w-64 animate-pulse bg-dalock-surface rounded-md" />}>
        <TableToolbar
          initialYear={params.year}
          initialBranchName={params.branch_name}
        />
      </Suspense>
      <Suspense fallback={<TableSkeleton />}>
        <BranchDataTable
          data={salesData.data}
          total={salesData.total}
          page={salesData.page}
          limit={salesData.limit}
          sortBy={params.sort_by ?? "sale_date"}
          order={(params.order as "asc" | "desc") ?? "desc"}
        />
      </Suspense>
    </div>
  );
}
