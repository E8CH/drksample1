import type { LandInfoData, LandPriceEntry } from "./definitions";

const VWORLD_KEY = process.env.NEXT_PUBLIC_VWORLD_API_KEY ?? "";
const VWORLD_2D_DATA = "https://api.vworld.kr/req/data";
const VWORLD_NED_ATTR = "https://api.vworld.kr/ned/data/getIndvdLandPriceAttr";
const LAND_BBOX_DELTA = 0.0003;

function extractLandType(jibun: string): string {
  const m = jibun.match(/[가-힣]+$/);
  return m ? m[0] : "";
}

export async function fetchLandInfo(lat: number, lon: number): Promise<LandInfoData> {
  if (!VWORLD_KEY) return { error: "VWORLD API 키 미설정" };

  const d = LAND_BBOX_DELTA;
  const geomFilter = `BOX(${lon - d},${lat - d},${lon + d},${lat + d})`;

  try {
    // Step 1: 필지 폴리곤 + 현재 공시지가
    const dataUrl = new URL(VWORLD_2D_DATA);
    dataUrl.searchParams.set("service", "data");
    dataUrl.searchParams.set("version", "2.0");
    dataUrl.searchParams.set("request", "GetFeature");
    dataUrl.searchParams.set("data", "LP_PA_CBND_BUBUN");
    dataUrl.searchParams.set("geomFilter", geomFilter);
    dataUrl.searchParams.set("crs", "EPSG:4326");
    dataUrl.searchParams.set("format", "json");
    dataUrl.searchParams.set("size", "1");
    dataUrl.searchParams.set("key", VWORLD_KEY);

    const dataResp = await fetch(dataUrl.toString());
    if (!dataResp.ok) return { error: "필지 데이터 로드 실패" };

    const dataJson = await dataResp.json();
    if (dataJson?.response?.status !== "OK") return { error: "해당 위치의 필지 정보가 없습니다" };

    const features = dataJson.response?.result?.featureCollection?.features ?? [];
    if (!features.length) return { error: "해당 위치의 필지 정보가 없습니다" };

    const feature = features[0];
    const props = feature.properties ?? {};
    const pnu: string = props.pnu ?? "";
    const currentPrice: number = Number(props.jiga ?? 0);
    const stdYear: string = String(props.gosi_year ?? "");
    const landType: string = extractLandType(props.jibun ?? "");
    const polygon: object | null = feature.geometry ?? null;

    // Step 2: 연도별 공시지가 히스토리
    let priceHistory: LandPriceEntry[] = [];
    if (pnu) {
      try {
        const attrUrl = new URL(VWORLD_NED_ATTR);
        attrUrl.searchParams.set("pnu", pnu);
        attrUrl.searchParams.set("format", "json");
        attrUrl.searchParams.set("numOfRows", "100");
        attrUrl.searchParams.set("key", VWORLD_KEY);

        const attrResp = await fetch(attrUrl.toString());
        if (attrResp.ok) {
          const attrJson = await attrResp.json();
          let items = attrJson?.indvdLandPrices?.field ?? [];
          if (!Array.isArray(items)) items = [items];
          priceHistory = (items as Record<string, string>[])
            .filter((item) => item.stdrYear && item.pblntfPclnd)
            .map((item) => ({
              year: Number(item.stdrYear),
              price_per_sqm: Number(item.pblntfPclnd),
            }))
            .sort((a, b) => a.year - b.year);
        }
      } catch {
        // 히스토리 실패는 무시 — 현재 가격만 표시
      }
    }

    return {
      pnu,
      current_price_per_sqm: currentPrice,
      std_year: stdYear,
      land_area_sqm: 0,
      land_type: landType,
      polygon,
      price_history: priceHistory,
    };
  } catch (e) {
    console.error("fetchLandInfo error:", e);
    return { error: "필지 정보 로드 실패" };
  }
}
