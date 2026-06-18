/**
 * VWORLD Proxy — Cloudflare Worker
 *
 * Smart Placement(wrangler.toml)로 서울 PoP에서 실행되어
 * api.vworld.kr 에 한국 IP로 요청을 전달합니다.
 *
 * 허용 경로:
 *   /req/data            → VWORLD 2D Data API (필지 폴리곤 + 공시지가)
 *   /ned/data/*          → VWORLD NED Attr API (연도별 공시지가)
 */

const VWORLD_HOST = "https://api.vworld.kr";
const SERVICE_REFERER = "https://frontend-production-7e58.up.railway.app/dashboard/simulation";
const ALLOWED_PATHS = ["/req/data", "/ned/data/"];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 허용된 경로만 프록시
    const isAllowed = ALLOWED_PATHS.some((p) => url.pathname.startsWith(p));
    if (!isAllowed) {
      return new Response("Not Found", { status: 404 });
    }

    // 선택적 공유 시크릿 검증 (Railway env에 PROXY_SECRET 설정 시 활성화)
    if (env.PROXY_SECRET) {
      const incoming = request.headers.get("X-Proxy-Secret") ?? "";
      if (incoming !== env.PROXY_SECRET) {
        return new Response("Forbidden", { status: 403 });
      }
    }

    const targetUrl = VWORLD_HOST + url.pathname + url.search;

    try {
      const vworldResp = await fetch(targetUrl, {
        method: request.method,
        headers: {
          Referer: SERVICE_REFERER,
          "User-Agent": "drksample1-proxy/1.0",
        },
      });

      return new Response(vworldResp.body, {
        status: vworldResp.status,
        headers: {
          "Content-Type": vworldResp.headers.get("Content-Type") ?? "application/json",
          "Cache-Control": "no-store",
        },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: String(err) }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }
  },
};
