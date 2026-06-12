"use client";
import { useState } from "react";
import { type SimulationResultData } from "@/lib/definitions";
import SimulationForm from "./SimulationForm";
import SimulationResultCard from "./SimulationResultCard";

export default function SimulationContainer() {
  const [result, setResult] = useState<SimulationResultData | null>(null);
  const [resultVersion, setResultVersion] = useState(0);

  function handleResult(r: SimulationResultData) {
    setResult(r);
    setResultVersion((v) => v + 1);
  }

  return (
    <div className="flex flex-col lg:flex-row min-h-[calc(100vh-56px)]">
      {/* Left panel — input form */}
      <div className="w-full lg:w-[320px] xl:w-[380px] shrink-0 bg-white border-r border-dalock-border p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold text-dalock-text1 mb-6">입지 조건 입력</h2>
        <SimulationForm onResult={handleResult} />
      </div>

      {/* Right panel — result or placeholder */}
      <div className="flex-1 bg-dalock-surface min-h-[300px]">
        {result ? (
          <SimulationResultCard key={resultVersion} result={result} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-dalock-text2 text-sm">지도 영역 — Story 3에서 구현 예정</p>
          </div>
        )}
      </div>
    </div>
  );
}
