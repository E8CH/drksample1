"use server";
import { cookies } from "next/headers";
import { type MapPinsData, type BuildingInfoData, type LandInfoData, type RentData, type AreaRentData } from "@/lib/definitions";

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

export async function fetchBuildingInfo(address: string): Promise<BuildingInfoData> {
  if (!address.trim()) return { error: "주소가 비어 있습니다" };
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { error: "인증이 필요합니다" };

  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const url = `${apiUrl}/building/info?address=${encodeURIComponent(address)}`;

  let res: Response;
  try {
    res = await fetch(url, {
      headers: { Cookie: `access_token=${token}` },
      cache: "no-store",
    });
  } catch {
    return { error: "건물 정보 서버 연결에 실패했습니다" };
  }

  if (res.status === 401) return { error: "인증이 만료되었습니다" };
  if (res.status === 404) return { error: "건물 정보를 찾을 수 없습니다" };
  if (res.status === 503) return { error: "건물 API 미설정" };
  if (!res.ok) return { error: "건물 정보 로드 실패" };

  return res.json();
}

export async function fetchLandInfo(lat: number, lon: number, name?: string): Promise<LandInfoData> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { error: "인증이 필요합니다" };

  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
  if (name) params.set("name", name);
  const url = `${apiUrl}/building/land?${params}`;

  let res: Response;
  try {
    res = await fetch(url, {
      headers: { Cookie: `access_token=${token}` },
      cache: "no-store",
    });
  } catch {
    return { error: "필지 정보 서버 연결에 실패했습니다" };
  }

  if (res.status === 401) return { error: "인증이 만료되었습니다" };
  if (res.status === 503) return { error: "VWORLD API 미설정" };
  if (res.status === 404) return { error: "해당 위치의 필지 정보가 없습니다" };
  if (!res.ok) return { error: "필지 정보 로드 실패" };

  return res.json();
}

export async function fetchBuildingRent(sigunguCd: string, bun: string, name: string): Promise<RentData> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { error: "인증이 필요합니다" };

  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const params = new URLSearchParams({ sigungu_cd: sigunguCd, bun, name });
  const url = `${apiUrl}/building/rent?${params}`;

  let res: Response;
  try {
    res = await fetch(url, { headers: { Cookie: `access_token=${token}` }, cache: "no-store" });
  } catch {
    return { error: "실거래가 서버 연결 실패" };
  }

  if (res.status === 401) return { error: "인증이 만료되었습니다" };
  if (res.status === 503) return { error: "API 키 미설정" };
  if (!res.ok) return { error: "실거래가 로드 실패" };
  return res.json();
}

export async function fetchAreaRent(sigunguCd: string): Promise<AreaRentData> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { error: "인증이 필요합니다" };

  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const url = `${apiUrl}/building/area-rent?sigungu_cd=${encodeURIComponent(sigunguCd)}`;

  let res: Response;
  try {
    res = await fetch(url, { headers: { Cookie: `access_token=${token}` }, cache: "no-store" });
  } catch {
    return { error: "임대동향 서버 연결 실패" };
  }

  if (res.status === 401) return { error: "인증이 만료되었습니다" };
  if (res.status === 503) return { error: "REB_KEY 미설정" };
  if (!res.ok) return { error: "임대동향 로드 실패" };
  return res.json();
}

export async function fetchMapPinsByCoords(
  lat: number,
  lon: number,
  radiusKm: number = 2.0
): Promise<MapPinsData> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { error: "인증이 필요합니다" };

  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  const url = `${apiUrl}/branches/nearby?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`;

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
  if (!res.ok) return { error: "지도 데이터 로드 실패" };

  const data = await res.json();
  if (!data?.target) return { error: "지도 응답 형식 오류" };
  return { target: data.target, pins: data.pins ?? [] };
}
