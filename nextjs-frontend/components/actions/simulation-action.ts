"use server";
import { type SimulationInput } from "@/lib/definitions";

export async function runSimulation(
  _input: SimulationInput
): Promise<{ error?: string }> {
  // Story 2-2에서 POST /simulation/run API 연결 예정
  await new Promise((r) => setTimeout(r, 1500));
  return {};
}
