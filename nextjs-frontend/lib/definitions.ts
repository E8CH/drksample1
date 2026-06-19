import { z } from "zod";

const passwordSchema = z
  .string()
  .min(8, "Password should be at least 8 characters.") // Minimum length validation
  .refine((password) => /[A-Z]/.test(password), {
    message: "Password should contain at least one uppercase letter.",
  }) // At least one uppercase letter
  .refine((password) => /[!@#$%^&*(),.?":{}|<>]/.test(password), {
    message: "Password should contain at least one special character.",
  });

export const passwordResetConfirmSchema = z
  .object({
    password: passwordSchema,
    passwordConfirm: z.string(),
    token: z.string({ required_error: "Token is required" }),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Passwords must match.",
    path: ["passwordConfirm"],
  });

export const registerSchema = z.object({
  password: passwordSchema,
  email: z.string().email({ message: "Invalid email address" }),
});

export const loginSchema = z.object({
  password: z.string().min(1, { message: "Password is required" }),
  username: z.string().min(1, { message: "Username is required" }),
});

export const simulationInputSchema = z.object({
  address: z.string().min(1, "주소를 입력하세요"),
  areaSqm: z.coerce
    .number({ invalid_type_error: "숫자를 입력하세요" })
    .positive("0보다 커야 합니다"),
  monthlyRent: z.coerce
    .number({ invalid_type_error: "숫자를 입력하세요" })
    .positive("0보다 커야 합니다"),
  maintenanceFee: z.coerce
    .number({ invalid_type_error: "숫자를 입력하세요" })
    .nonnegative()
    .optional(),
  buildingUse: z.enum(["상업용", "근린생활시설", "창고", "기타"]).optional(),
  evCharging: z.boolean().optional().default(false),
  parkingSpots: z.coerce
    .number({ invalid_type_error: "숫자를 입력하세요" })
    .int()
    .nonnegative()
    .optional(),
});

export type SimulationInput = z.infer<typeof simulationInputSchema>;

export type ComparisonEntry = {
  name: string;
  monthly_revenue: number;
};

export type SimulationResultData = {
  estimated_monthly_revenue: number;
  occupancy_rate: number;
  net_profit: number;
  percentile: number;
  verdict: "추천" | "검토필요" | "비추천";
  similar_branch_count: number;
  fallback_used: boolean;
  comparison_data: ComparisonEntry[];
};

export type SalesRow = {
  branch_name: string;
  address: string;
  sale_month: string;
  monthly_revenue: number;
  electricity_fee: number;
  operating_cost: number;
  net_profit: number;
  occupancy_rate: number;
};

export type SalesListResponse = {
  data: SalesRow[];
  total: number;
  page: number;
  limit: number;
};

export type BranchPinData = {
  branch_name: string;
  address: string;
  latitude: number;
  longitude: number;
};

export type MapPinsData =
  | { target: { latitude: number; longitude: number }; pins: BranchPinData[] }
  | { error: string };

export type BuildingUnit = {
  ho: string;
  floor: string;
  purpose: string;
  exclusive_sqm: number;
  exclusive_py: number;
  common_sqm: number;
};

export type BuildingInfoData =
  | {
      found: true;
      road_address: string;
      jibun_address: string;
      latitude: number | null;
      longitude: number | null;
      building_name: string;
      total_floors: number;
      underground_floors: number;
      total_area_sqm: number;
      total_units: number;
      main_purpose: string;
      units: BuildingUnit[];
      sigungu_cd: string;
      bun: string;
    }
  | { found: false; road_address: string; jibun_address: string }
  | { error: string };

export type RentTransaction = {
  date: string;
  amount_wan: number;
  floor: string;
  area_sqm: number;
  building_name: string;
  land_use: string;
};

export type RentData =
  | { transactions: RentTransaction[] }
  | { error: string };

export type AreaRentOfficeArea = {
  name: string;
  office_rent_kwon_sqm: number | null;
  office_vacancy_pct: number | null;
};

export type AreaRentMallArea = {
  name: string;
  mall_rent_kwon_sqm: number | null;
};

export type AreaRentData =
  | {
      quarter: string;
      sido: string;
      office_areas: AreaRentOfficeArea[];
      mall_areas: AreaRentMallArea[];
      has_data: boolean;
    }
  | { error: string };

export type LandPriceEntry = {
  year: number;
  price_per_sqm: number;
};

export type LandInfoData =
  | {
      pnu: string;
      current_price_per_sqm: number;
      std_year: string;
      land_area_sqm: number;
      land_type: string;
      polygon: object | null;
      price_history: LandPriceEntry[];
    }
  | { error: string };

export const itemSchema = z.object({
  name: z.string().min(1, { message: "Name is required" }),
  description: z.string().min(1, { message: "Description is required" }),
  quantity: z
    .string()
    .min(1, { message: "Quantity is required" })
    .transform((val) => parseInt(val, 10)) // Convert to integer
    .refine((val) => Number.isInteger(val) && val > 0, {
      message: "Quantity must be a positive integer",
    }),
});
