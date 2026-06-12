"use server";
import { cookies } from "next/headers";
import { type MapPinsData } from "@/lib/definitions";

export async function fetchMapPins(address: string): Promise<MapPinsData> {
  if (!address.trim()) return { error: "주소가 비어 있습니다" };
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { error: "인증이 필요합니다" };

  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const url = `${apiUrl}/branches/nearby?address=${encodeURIComponent(address)}&radius_km=2.0`;

  let res: Response;
  try {
    res = await fetch(url, {
      headers: { Cookie: `access_token=${token}` },
      cache: "no-store",
    });
  } catch {
    return { error: "지도 서버 연결에 실패했습니다" };
  }

  if (res.status === 401) return { error: "인증이 만료되었습니다" };
  if (res.status === 422) return { error: "주소를 변환할 수 없습니다" };
  if (!res.ok) return { error: "지도 데이터 로드 실패" };

  const data = await res.json();
  if (!data?.target) return { error: "지도 응답 형식 오류" };
  return { target: data.target, pins: data.pins ?? [] };
}
