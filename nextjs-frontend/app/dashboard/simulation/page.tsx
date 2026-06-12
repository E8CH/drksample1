export default function SimulationPage() {
  return (
    <div className="flex flex-col lg:flex-row min-h-[calc(100vh-56px)]">
      <div className="w-full lg:w-[320px] xl:w-[380px] shrink-0 bg-white border-r border-dalock-border p-6 overflow-y-auto">
        <h2 className="text-xl font-semibold text-dalock-text1 mb-4">입지 조건 입력</h2>
        <p className="text-dalock-text2 text-sm">Story 2에서 구현 예정</p>
      </div>
      <div className="flex-1 bg-dalock-surface flex items-center justify-center min-h-[300px]">
        <p className="text-dalock-text2 text-sm">지도 영역 — Story 3에서 구현 예정</p>
      </div>
    </div>
  );
}
