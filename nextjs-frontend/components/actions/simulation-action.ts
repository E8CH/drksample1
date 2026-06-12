"use server";
import { cookies } from "next/headers";
import { type SimulationInput, type SimulationResultData } from "@/lib/definitions";

export type SimulationActionResult =
  | { error: string; result?: undefined }
  | { result: SimulationResultData; error?: undefined };

export async function runSimulation(input: SimulationInput): Promise<SimulationActionResult> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) {
    return { error: "인증이 필요합니다" };
  }

  const apiUrl = process.env.API_URL ?? "http://localhost:8000";

  let res: Response;
  try {
    res = await fetch(`${apiUrl}/simulation/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Cookie: `access_token=${token}`,
      },
      body: JSON.stringify({
        address: input.address,
        area_sqm: input.areaSqm,
        monthly_rent: input.monthlyRent,
        monthly_maintenance: input.maintenanceFee ?? null,
        building_usage: input.buildingUse ?? null,
        ev_charging: input.evCharging ?? false,
        parking_count: input.parkingSpots ?? 0,
      }),
    });
  } catch {
    return { error: "서버 연결에 실패했습니다" };
  }

  if (res.status === 401) {
    return { error: "인증이 만료되었습니다. 다시 로그인해 주세요." };
  }
  if (!res.ok) {
    return { error: "시뮬레이션 오류가 발생했습니다" };
  }

  const data = (await res.json()) as SimulationResultData;
  const VALID_VERDICTS: SimulationResultData["verdict"][] = ["추천", "검토필요", "비추천"];
  if (!data?.verdict || !VALID_VERDICTS.includes(data.verdict)) {
    return { error: "서버 응답 형식 오류가 발생했습니다" };
  }
  return { result: data };
}
