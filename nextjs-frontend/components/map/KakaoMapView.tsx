"use client";
import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { divIcon } from "leaflet";
import { type BranchPinData } from "@/lib/definitions";

type Props = {
  address: string;
  target: { latitude: number; longitude: number } | null;
  pins: BranchPinData[];
};

const targetIcon = divIcon({
  className: "",
  html: '<span style="font-size:24px;color:#2563EB;text-shadow:0 1px 3px rgba(0,0,0,0.4);line-height:1;">★</span>',
  iconAnchor: [12, 12],
  iconSize: [24, 24],
});

const branchIcon = divIcon({
  className: "",
  html: '<span style="font-size:16px;color:#94A3B8;text-shadow:0 1px 2px rgba(0,0,0,0.3);line-height:1;">●</span>',
  iconAnchor: [8, 8],
  iconSize: [16, 16],
});

export default function KakaoMapView({ address, target, pins }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
  }, []);

  if (!target) {
    return (
      <div className="flex items-center justify-center h-full bg-dalock-surface">
        <p className="text-dalock-text2 text-sm">주소: {address}</p>
      </div>
    );
  }

  return (
    <div
      aria-label="카카오맵 — 분석 위치 및 인근 지점 표시"
      className={`h-full w-full transition-opacity duration-300 ${visible ? "opacity-100" : "opacity-0"}`}
    >
      <MapContainer
        center={[target.latitude, target.longitude]}
        zoom={15}
        style={{ height: "100%", width: "100%" }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <Marker position={[target.latitude, target.longitude]} icon={targetIcon}>
          <Popup>분석 대상 위치</Popup>
        </Marker>
        {pins.map((pin) => (
          <Marker
            key={pin.branch_name}
            position={[pin.latitude, pin.longitude]}
            icon={branchIcon}
          >
            <Popup>{pin.branch_name}</Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
