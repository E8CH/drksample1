"use client";
// Must be loaded via dynamic({ ssr: false }) — Leaflet requires browser globals.
import "leaflet/dist/leaflet.css";
import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from "react-leaflet";
import { divIcon, geoJSON as leafletGeoJSON } from "leaflet";
import { type BranchPinData } from "@/lib/definitions";

function MapCenter({ target }: { target: { latitude: number; longitude: number } | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.setView([target.latitude, target.longitude], 17);
  }, [map, target]);
  return null;
}

function PolygonFit({ polygon }: { polygon: object | null }) {
  const map = useMap();
  useEffect(() => {
    if (!polygon) return;
    try {
      const bounds = leafletGeoJSON(polygon as Parameters<typeof leafletGeoJSON>[0]).getBounds();
      if (bounds.isValid()) map.setView(bounds.getCenter(), 19);
    } catch {}
  }, [map, polygon]);
  return null;
}

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
        html: `<svg width="28" height="40" viewBox="0 0 28 40" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="14" cy="38" rx="5" ry="2" fill="rgba(0,0,0,0.18)"/>
          <path d="M14 1C7.92 1 3 5.92 3 12c0 8.5 11 25 11 25S25 20.5 25 12C25 5.92 20.08 1 14 1z" fill="#2563EB" stroke="white" stroke-width="1.5"/>
          <circle cx="14" cy="12" r="5" fill="white"/>
        </svg>`,
        iconAnchor: [14, 40],
        iconSize: [28, 40],
      }),
    []
  );

  const branchIcon = useMemo(
    () =>
      divIcon({
        className: "",
        html: `<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <circle cx="10" cy="10" r="8" fill="#EF4444" stroke="white" stroke-width="2"/>
          <line x1="10" y1="5" x2="10" y2="15" stroke="white" stroke-width="2" stroke-linecap="round"/>
          <line x1="5" y1="10" x2="15" y2="10" stroke="white" stroke-width="2" stroke-linecap="round"/>
        </svg>`,
        iconAnchor: [10, 10],
        iconSize: [20, 20],
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
        zoom={target ? 17 : 11}
        style={{ height: "100%", width: "100%" }}
        zoomControl={true}
      >
        <MapCenter target={target} />
        <PolygonFit polygon={polygon ?? null} />
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
