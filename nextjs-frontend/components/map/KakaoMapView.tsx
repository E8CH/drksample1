"use client";
// Must be loaded via dynamic({ ssr: false }) — Leaflet requires browser globals.
import "leaflet/dist/leaflet.css";
import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, GeoJSON } from "react-leaflet";
import { divIcon } from "leaflet";
import { type BranchPinData } from "@/lib/definitions";

type Props = {
  address: string;
  target: { latitude: number; longitude: number } | null;
  pins: BranchPinData[];
  error?: string | null;
  polygon?: object | null;
};

export default function KakaoMapView({ address, target, pins, error, polygon }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
  }, []);

  const targetIcon = useMemo(
    () =>
      divIcon({
        className: "",
        html: '<span style="font-size:24px;color:#2563EB;text-shadow:0 1px 3px rgba(0,0,0,0.4);line-height:1;">★</span>',
        iconAnchor: [12, 12],
        iconSize: [24, 24],
      }),
    []
  );

  const branchIcon = useMemo(
    () =>
      divIcon({
        className: "",
        html: '<span style="font-size:16px;color:#94A3B8;text-shadow:0 1px 2px rgba(0,0,0,0.3);line-height:1;">●</span>',
        iconAnchor: [8, 8],
        iconSize: [16, 16],
      }),
    []
  );

  // 서울 기본 좌표 — target 없을 때 Leaflet이 미리 초기화되도록 항상 MapContainer 렌더
  const center: [number, number] = target
    ? [target.latitude, target.longitude]
    : [37.5665, 126.978];

  return (
    <div
      role="region"
      aria-label="카카오맵 — 분석 위치 및 인근 지점 표시"
      className={`h-full w-full isolate transition-opacity duration-300 ${visible ? "opacity-100" : "opacity-0"}`}
    >
      <MapContainer
        center={center}
        zoom={target ? 15 : 11}
        style={{ height: "100%", width: "100%" }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {polygon && (
          <GeoJSON
            key={JSON.stringify(polygon)}
            data={polygon as Parameters<typeof GeoJSON>[0]["data"]}
            style={{ color: "#2563EB", weight: 2, fillColor: "#3B82F6", fillOpacity: 0.25 }}
          />
        )}
        {target && (
          <>
            <Marker position={[target.latitude, target.longitude]} icon={targetIcon}>
              <Popup>분석 대상 위치</Popup>
            </Marker>
            {pins.map((pin) => (
              <Marker
                key={`${pin.branch_name}-${pin.latitude}-${pin.longitude}`}
                position={[pin.latitude, pin.longitude]}
                icon={branchIcon}
              >
                <Popup>{pin.branch_name}</Popup>
              </Marker>
            ))}
          </>
        )}
      </MapContainer>
      {!target && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-dalock-surface/80 gap-2 pointer-events-none">
          {error && (
            <p className="text-dalock-danger text-sm">지오코딩 실패: 주소를 확인해 주세요</p>
          )}
          {error && <p className="text-dalock-text2 text-sm">주소: {address}</p>}
        </div>
      )}
    </div>
  );
}
