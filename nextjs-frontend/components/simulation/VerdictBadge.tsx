import { type SimulationResultData } from "@/lib/definitions";

type Props = {
  verdict: SimulationResultData["verdict"];
  percentile: number;
};

const CONFIG = {
  추천: { icon: "✅", label: "추천", className: "bg-dalock-success text-white", rank: (p: number) => `상위 ${Math.min(99, Math.max(1, Math.round(100 - p)))}%` },
  검토필요: { icon: "⚠️", label: "검토필요", className: "bg-dalock-warning text-white", rank: (p: number) => `상위 ${Math.min(99, Math.max(1, Math.round(100 - p)))}%` },
  비추천: { icon: "❌", label: "비추천", className: "bg-dalock-danger text-white", rank: (p: number) => `하위 ${Math.min(99, Math.max(1, Math.round(p)))}%` },
} as const;

export default function VerdictBadge({ verdict, percentile }: Props) {
  const cfg = CONFIG[verdict] ?? CONFIG["검토필요"];
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold ${cfg.className}`}>
      {cfg.icon} {cfg.label} — {cfg.rank(percentile)}
    </span>
  );
}
