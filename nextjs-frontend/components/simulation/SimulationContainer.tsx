"use client";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { type SimulationResultData, type MapPinsData, type BranchPinData } from "@/lib/definitions";
import { fetchMapPins } from "@/components/actions/map-action";
import SimulationForm from "./SimulationForm";
import SimulationResultCard from "./SimulationResultCard";

const KakaoMapView = dynamic(
  () => import("@/components/map/KakaoMapView"),
  { ssr: false, loading: () => <div className="flex items-center justify-center h-full bg-dalock-surface"><p className="text-dalock-text2 text-sm">지도 로드 중...</p></div> }
);

export default function SimulationContainer() {
  const [result, setResult] = useState<SimulationResultData | null>(null);
  const [resultVersion, setResultVersion] = useState(0);
  const [mapAddress, setMapAddress] = useState<string | null>(null);
  const [mapTarget, setMapTarget] = useState<{ latitude: number; longitude: number } | null>(null);
  const [mapPins, setMapPins] = useState<BranchPinData[]>([]);

  useEffect(() => {
    if (!mapAddress) return;
    fetchMapPins(mapAddress).then((data: MapPinsData) => {
      if ("error" in data) {
        setMapTarget(null);
        setMapPins([]);
      } else {
        setMapTarget(data.target);
        setMapPins(data.pins);
      }
    });
  }, [mapAddress]);

  function handleResult(r: SimulationResultData, address: string) {
    setResult(r);
    setResultVersion((v) => v + 1);
    setMapAddress(address);
  }

  return (
    <div className="flex flex-col lg:flex-row min-h-[calc(100vh-56px)]">
      {/* Left panel — input form */}
      <div className="w-full lg:w-[320px] xl:w-[380px] shrink-0 bg-white border-r border-dalock-border p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold text-dalock-text1 mb-6">입지 조건 입력</h2>
        <SimulationForm onResult={handleResult} />
      </div>

      {/* Right panel — map + result overlay */}
      <div className="relative flex-1 bg-dalock-surface min-h-[300px]">
        {mapAddress ? (
          <KakaoMapView
            address={mapAddress}
            target={mapTarget}
            pins={mapPins}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-dalock-text2 text-sm">주소를 입력하고 시뮬레이션을 실행하세요</p>
          </div>
        )}

        {/* Result card overlay — bottom-right of map */}
        {result && (
          <div className="absolute bottom-4 right-4 w-72 max-h-[calc(100%-2rem)] overflow-y-auto rounded-xl shadow-xl bg-white">
            <SimulationResultCard key={resultVersion} result={result} />
          </div>
        )}
      </div>
    </div>
  );
}
