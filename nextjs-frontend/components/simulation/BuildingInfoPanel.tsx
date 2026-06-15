"use client";
import { type BuildingInfoData } from "@/lib/definitions";

type Props = {
  data: BuildingInfoData | null;
  loading: boolean;
};

function SkeletonRow() {
  return <div className="h-4 bg-dalock-surface rounded animate-pulse mb-2" />;
}

export default function BuildingInfoPanel({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2 pt-1">
        <SkeletonRow />
        <SkeletonRow />
        <div className="grid grid-cols-3 gap-2 mt-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-12 bg-dalock-surface rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  if ("error" in data) {
    return (
      <p className="text-xs text-dalock-text2">{data.error}</p>
    );
  }

  if (!data.found) {
    return (
      <p className="text-xs text-dalock-text2">
        해당 주소의 건축물대장 정보가 없습니다
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {/* 건물 개요 */}
      <div>
        <p className="text-sm font-semibold text-dalock-text1">
          {data.building_name || "건물명 미등록"}
        </p>
        <p className="text-xs text-dalock-text2 mt-0.5">{data.jibun_address}</p>
        {data.main_purpose && (
          <span className="inline-block mt-1 text-xs bg-blue-50 text-blue-700 rounded px-2 py-0.5">
            {data.main_purpose}
          </span>
        )}

        <div className="grid grid-cols-3 gap-2 mt-3">
          <div className="bg-dalock-surface rounded-lg p-2 text-center">
            <p className="text-xs text-dalock-text2">지상/지하</p>
            <p className="text-sm font-semibold mt-0.5">
              {data.total_floors}F
              {data.underground_floors > 0 && (
                <span className="text-xs font-normal text-dalock-text2">
                  {" "}/ B{data.underground_floors}
                </span>
              )}
            </p>
          </div>
          <div className="bg-dalock-surface rounded-lg p-2 text-center">
            <p className="text-xs text-dalock-text2">연면적</p>
            <p className="text-sm font-semibold mt-0.5">
              {data.total_area_sqm.toLocaleString("ko-KR", { maximumFractionDigits: 0 })}
              <span className="text-xs font-normal text-dalock-text2">㎡</span>
            </p>
          </div>
          <div className="bg-dalock-surface rounded-lg p-2 text-center">
            <p className="text-xs text-dalock-text2">세대수</p>
            <p className="text-sm font-semibold mt-0.5">
              {data.total_units}
              <span className="text-xs font-normal text-dalock-text2">세대</span>
            </p>
          </div>
        </div>
      </div>

      {/* 호수별 전용면적 */}
      {data.units.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-dalock-text2 mb-2">
            호수별 전용면적 ({data.units.length}호)
          </p>
          <div className="max-h-52 overflow-y-auto rounded-lg border border-dalock-border">
            <table className="w-full text-xs">
              <thead className="bg-dalock-surface sticky top-0">
                <tr>
                  <th className="text-left px-2 py-1.5 text-dalock-text2 font-medium">호수</th>
                  <th className="text-left px-2 py-1.5 text-dalock-text2 font-medium">용도</th>
                  <th className="text-right px-2 py-1.5 text-dalock-text2 font-medium">전용</th>
                </tr>
              </thead>
              <tbody>
                {data.units.map((u, i) => (
                  <tr
                    key={i}
                    className="border-t border-dalock-border hover:bg-dalock-surface/50"
                  >
                    <td className="px-2 py-1.5 font-medium text-dalock-text1">{u.ho}</td>
                    <td className="px-2 py-1.5 text-dalock-text2 truncate max-w-[80px]">
                      {u.purpose || "—"}
                    </td>
                    <td className="px-2 py-1.5 text-right text-dalock-text1">
                      {u.exclusive_py}
                      <span className="text-dalock-text2">평</span>
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
