"use client";
import { useState, useTransition } from "react";
import { simulationInputSchema } from "@/lib/definitions";
import { runSimulation } from "@/components/actions/simulation-action";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type FieldValues = {
  address: string;
  areaSqm: string;
  monthlyRent: string;
  maintenanceFee: string;
  buildingUse: string;
  evCharging: boolean;
  parkingSpots: string;
};

const INITIAL_VALUES: FieldValues = {
  address: "",
  areaSqm: "",
  monthlyRent: "",
  maintenanceFee: "",
  buildingUse: "",
  evCharging: false,
  parkingSpots: "",
};

type ValidatorFn = (v: unknown) => { success: boolean; error?: { issues: { message: string }[] } };

const fieldValidators: Record<string, ValidatorFn> = {
  address: (v) => simulationInputSchema.pick({ address: true }).safeParse({ address: v }) as ReturnType<ValidatorFn>,
  areaSqm: (v) => simulationInputSchema.pick({ areaSqm: true }).safeParse({ areaSqm: v }) as ReturnType<ValidatorFn>,
  monthlyRent: (v) => simulationInputSchema.pick({ monthlyRent: true }).safeParse({ monthlyRent: v }) as ReturnType<ValidatorFn>,
  maintenanceFee: (v) => simulationInputSchema.pick({ maintenanceFee: true }).safeParse({ maintenanceFee: v || undefined }) as ReturnType<ValidatorFn>,
  parkingSpots: (v) => simulationInputSchema.pick({ parkingSpots: true }).safeParse({ parkingSpots: v || undefined }) as ReturnType<ValidatorFn>,
};

function validateField(name: string, value: string | boolean): string | undefined {
  const validator = fieldValidators[name];
  if (!validator) return undefined;
  const result = validator(value);
  if (!result.success && result.error) {
    return result.error.issues[0]?.message;
  }
  return undefined;
}

function inputClass(error?: string) {
  return error ? "border-dalock-danger focus-visible:ring-dalock-danger" : "";
}

export default function SimulationForm() {
  const [isPending, startTransition] = useTransition();
  const [values, setValues] = useState<FieldValues>(INITIAL_VALUES);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string | null>(null);

  const isSubmitDisabled =
    !values.address.trim() ||
    !(Number(values.areaSqm) > 0) ||
    !(Number(values.monthlyRent) > 0) ||
    isPending;

  function setField(name: keyof FieldValues, value: string | boolean) {
    setValues((prev) => ({ ...prev, [name]: value }));
    if (errors[name] !== undefined) {
      const error = validateField(name, value as string);
      setErrors((prev) => {
        const next = { ...prev };
        if (error) next[name] = error;
        else delete next[name];
        return next;
      });
    }
  }

  function handleBlur(name: string, value: string | boolean) {
    const error = validateField(name, value);
    setErrors((prev) => {
      const next = { ...prev };
      if (error) next[name] = error;
      else delete next[name];
      return next;
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setServerError(null);

    const parsed = simulationInputSchema.safeParse({
      address: values.address.trim(),
      areaSqm: values.areaSqm,
      monthlyRent: values.monthlyRent,
      maintenanceFee: values.maintenanceFee || undefined,
      buildingUse: values.buildingUse || undefined,
      evCharging: values.evCharging,
      parkingSpots: values.parkingSpots || undefined,
    });

    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0] as string;
        if (!fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    startTransition(() => {
      runSimulation(parsed.data).then((res) => {
        if (res.error) setServerError(res.error);
      });
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {/* 주소 */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="address" className="text-dalock-text1 text-sm font-medium">
          주소 <span className="text-dalock-danger">*</span>
        </Label>
        <Input
          id="address"
          name="address"
          type="text"
          placeholder="예: 서울 강남구 역삼동 123"
          value={values.address}
          onChange={(e) => setField("address", e.target.value)}
          onBlur={(e) => handleBlur("address", e.target.value)}
          className={inputClass(errors.address)}
          disabled={isPending}
        />
        {errors.address && (
          <p className="text-dalock-danger text-xs">{errors.address}</p>
        )}
      </div>

      {/* 면적 */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="areaSqm" className="text-dalock-text1 text-sm font-medium">
          면적(㎡) <span className="text-dalock-danger">*</span>
        </Label>
        <Input
          id="areaSqm"
          name="areaSqm"
          type="text"
          inputMode="decimal"
          placeholder="예: 150"
          value={values.areaSqm}
          onChange={(e) => setField("areaSqm", e.target.value)}
          onBlur={(e) => handleBlur("areaSqm", e.target.value)}
          className={inputClass(errors.areaSqm)}
          disabled={isPending}
        />
        {errors.areaSqm && (
          <p className="text-dalock-danger text-xs">{errors.areaSqm}</p>
        )}
      </div>

      {/* 월 임대료 */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="monthlyRent" className="text-dalock-text1 text-sm font-medium">
          월 임대료(만원) <span className="text-dalock-danger">*</span>
        </Label>
        <Input
          id="monthlyRent"
          name="monthlyRent"
          type="text"
          inputMode="decimal"
          placeholder="예: 200"
          value={values.monthlyRent}
          onChange={(e) => setField("monthlyRent", e.target.value)}
          onBlur={(e) => handleBlur("monthlyRent", e.target.value)}
          className={inputClass(errors.monthlyRent)}
          disabled={isPending}
        />
        {errors.monthlyRent && (
          <p className="text-dalock-danger text-xs">{errors.monthlyRent}</p>
        )}
      </div>

      {/* 관리비 */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="maintenanceFee" className="text-dalock-text1 text-sm font-medium">
          관리비(만원)
        </Label>
        <Input
          id="maintenanceFee"
          name="maintenanceFee"
          type="text"
          inputMode="decimal"
          placeholder="예: 30"
          value={values.maintenanceFee}
          onChange={(e) => setField("maintenanceFee", e.target.value)}
          onBlur={(e) => handleBlur("maintenanceFee", e.target.value)}
          className={inputClass(errors.maintenanceFee)}
          disabled={isPending}
        />
        {errors.maintenanceFee && (
          <p className="text-dalock-danger text-xs">{errors.maintenanceFee}</p>
        )}
      </div>

      {/* 건축물용도 */}
      <div className="flex flex-col gap-1.5">
        <Label className="text-dalock-text1 text-sm font-medium">건축물용도</Label>
        <Select
          value={values.buildingUse}
          onValueChange={(v) => setField("buildingUse", v)}
          disabled={isPending}
        >
          <SelectTrigger>
            <SelectValue placeholder="선택하세요" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="상업용">상업용</SelectItem>
            <SelectItem value="근린생활시설">근린생활시설</SelectItem>
            <SelectItem value="창고">창고</SelectItem>
            <SelectItem value="기타">기타</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* EV충전 */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="evCharging"
          checked={values.evCharging}
          onChange={(e) => setField("evCharging", e.target.checked)}
          className="w-4 h-4 accent-dalock-primary"
          disabled={isPending}
        />
        <Label htmlFor="evCharging" className="text-dalock-text1 text-sm font-medium cursor-pointer">
          EV충전 가능
        </Label>
      </div>

      {/* 주차대수 */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="parkingSpots" className="text-dalock-text1 text-sm font-medium">
          주차 가능 대수
        </Label>
        <Input
          id="parkingSpots"
          name="parkingSpots"
          type="text"
          inputMode="numeric"
          placeholder="예: 10"
          value={values.parkingSpots}
          onChange={(e) => setField("parkingSpots", e.target.value)}
          onBlur={(e) => handleBlur("parkingSpots", e.target.value)}
          className={inputClass(errors.parkingSpots)}
          disabled={isPending}
        />
        {errors.parkingSpots && (
          <p className="text-dalock-danger text-xs">{errors.parkingSpots}</p>
        )}
      </div>

      {/* 서버 오류 */}
      {serverError && (
        <p className="text-dalock-danger text-sm text-center">{serverError}</p>
      )}

      {/* 제출 버튼 */}
      <button
        type="submit"
        disabled={isSubmitDisabled}
        className="mt-2 flex items-center justify-center gap-2 rounded-md bg-dalock-primary text-white text-sm font-medium px-4 py-2.5 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isPending && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {isPending ? "분석 중..." : "시뮬레이션 실행"}
      </button>
    </form>
  );
}
