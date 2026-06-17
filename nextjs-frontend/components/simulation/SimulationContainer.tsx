"use client";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  type SimulationResultData,
  type MapPinsData,
  type BranchPinData,
  type SimulationInput,
  type BuildingInfoData,
  type LandInfoData,
} from "@/lib/definitions";
import { fetchMapPins, fetchMapPinsByCoords, fetchBuildingInfo } from "@/components/actions/map-action";
import { geocodeAddress, fetchLandInfo } from "@/lib/vworld-client";
import SimulationForm from "./SimulationForm";
import SimulationResultCard from "./SimulationResultCard";
import BuildingInfoPanel from "./BuildingInfoPanel";
import LandInfoPanel from "./LandInfoPanel";
import ProposalModal from "@/components/proposal/ProposalModal";

const KakaoMapView = dynamic(
  () => import("@/components/map/KakaoMapView"),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full bg-dalock-surface">
        <p className="text-dalock-text2 text-sm">지도 로드 중...</p>
      </div>
    ),
  }
);

type MapRequest = { address: string; seq: number };

export default function SimulationContainer() {
  const [result, setResult] = useState<SimulationResultData | null>(null);
  const [resultVersion, setResultVersion] = useState(0);
  const [submittedInput, setSubmittedInput] = useState<SimulationInput | null>(null);
  const [proposalOpen, setProposalOpen] = useState(false);

  // Map fetch state — seq counter prevents same-address re-submit skip
  const [mapRequest, setMapRequest] = useState<MapRequest | null>(null);
  const [mapLoading, setMapLoading] = useState(false);
  const [mapTarget, setMapTarget] = useState<{ latitude: number; longitude: number } | null>(null);
  const [mapPins, setMapPins] = useState<BranchPinData[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);

  // Building info state
  const [buildingRequest, setBuildingRequest] = useState<MapRequest | null>(null);
  const [buildingLoading, setBuildingLoading] = useState(false);
  const [buildingInfo, setBuildingInfo] = useState<BuildingInfoData | null>(null);

  // Land info (필지 폴리곤 + 공시지가)
  type LandRequest = { lat: number; lon: number; seq: number };
  const [landRequest, setLandRequest] = useState<LandRequest | null>(null);
  const [landLoading, setLandLoading] = useState(false);
  const [landInfo, setLandInfo] = useState<LandInfoData | null>(null);

  useEffect(() => {
    if (!mapRequest) return;
    let cancelled = false;
    setMapLoading(true);
    setMapError(null);

    (async () => {
      // 1순위: 브라우저에서 VWORLD 지오코딩 (정확도 최고)
      const vworldCoords = await geocodeAddress(mapRequest.address);

      let data: MapPinsData;
      if (vworldCoords) {
        // VWORLD 좌표 → 서버에 lat/lon 전달 (지오코딩 스킵)
        data = await fetchMapPinsByCoords(vworldCoords.lat, vworldCoords.lon);
      } else {
        // 폴백: 서버사이드 지오코딩 (Nominatim)
        data = await fetchMapPins(mapRequest.address);
      }

      if (cancelled) return;
      setMapLoading(false);
      if ("error" in data) {
        setMapTarget(null);
        setMapPins([]);
        setMapError(data.error);
      } else {
        setMapTarget(data.target);
        setMapPins(data.pins);
        setLandRequest((prev) => ({
          lat: data.target.latitude,
          lon: data.target.longitude,
          seq: (prev?.seq ?? 0) + 1,
        }));
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [mapRequest]);

  useEffect(() => {
    if (!buildingRequest) return;
    let cancelled = false;
    setBuildingLoading(true);
    setBuildingInfo(null);
    fetchBuildingInfo(buildingRequest.address).then((data: BuildingInfoData) => {
      if (cancelled) return;
      setBuildingLoading(false);
      setBuildingInfo(data);
    });
    return () => {
      cancelled = true;
    };
  }, [buildingRequest]);

  useEffect(() => {
    if (!landRequest) return;
    let cancelled = false;
    setLandLoading(true);
    setLandInfo(null);
    fetchLandInfo(landRequest.lat, landRequest.lon).then((data: LandInfoData) => {
      if (cancelled) return;
      setLandLoading(false);
      setLandInfo(data);
    });
    return () => {
      cancelled = true;
    };
  }, [landRequest]);

  function handleResult(r: SimulationResultData, input: SimulationInput) {
    setResult(r);
    setSubmittedInput(input);
    setProposalOpen(false);
    setResultVersion((v) => v + 1);
    // seq always increments → same-address re-submit still triggers new fetch
    setMapRequest((prev) => ({ address: input.address, seq: (prev?.seq ?? 0) + 1 }));
    setBuildingRequest((prev) => ({ address: input.address, seq: (prev?.seq ?? 0) + 1 }));
  }

  return (
    <div className="flex flex-col lg:flex-row min-h-[calc(100vh-56px)]">
      {/* Left panel — input form + building info */}
      <div className="w-full lg:w-[320px] xl:w-[380px] shrink-0 bg-white border-r border-dalock-border p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold text-dalock-text1 mb-6">입지 조건 입력</h2>
        <SimulationForm onResult={handleResult} />

        {(buildingLoading || buildingInfo) && (
          <div className="mt-6 pt-6 border-t border-dalock-border">
            <h3 className="text-sm font-semibold text-dalock-text1 mb-3">건물 정보</h3>
            <BuildingInfoPanel data={buildingInfo} loading={buildingLoading} />
          </div>
        )}

        {(landLoading || landInfo) && (
          <div className="mt-6 pt-6 border-t border-dalock-border">
            <h3 className="text-sm font-semibold text-dalock-text1 mb-3">공시지가</h3>
            <LandInfoPanel data={landInfo} loading={landLoading} />
          </div>
        )}
      </div>

      {/* Right panel — map + result overlay */}
      <div className="relative flex-1 bg-dalock-surface min-h-[300px]">
        {mapRequest === null ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-dalock-text2 text-sm">주소를 입력하고 시뮬레이션을 실행하세요</p>
          </div>
        ) : (
          // 항상 마운트 — Leaflet이 지도 데이터 도착 전에 초기화되어 모달 간섭 방지
          <KakaoMapView
            key={resultVersion}
            address={mapRequest.address}
            target={mapLoading ? null : mapTarget}
            pins={mapLoading ? [] : mapPins}
            error={mapLoading ? null : mapError}
            polygon={landInfo && !("error" in landInfo) ? landInfo.polygon : null}
          />
        )}

        {/* Result card overlay — fixed size with mobile-safe max-w */}
        {result && (
          <div className="absolute bottom-4 right-4 w-72 max-w-[calc(100%-2rem)] max-h-[calc(100%-2rem)] overflow-y-auto rounded-xl shadow-xl bg-white z-[1000]">
            <SimulationResultCard
              key={resultVersion}
              result={result}
              onProposalClick={() => setProposalOpen(true)}
            />
          </div>
        )}
      </div>

      {/* Proposal modal */}
      {proposalOpen && result && submittedInput && (
        <ProposalModal
          open={proposalOpen}
          onClose={() => setProposalOpen(false)}
          result={result}
          input={submittedInput}
        />
      )}
    </div>
  );
}
