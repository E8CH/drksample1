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

export type SimulationResultData = {
  estimated_monthly_revenue: number;
  occupancy_rate: number;
  net_profit: number;
  percentile: number;
  verdict: "추천" | "검토필요" | "비추천";
  similar_branch_count: number;
  fallback_used: boolean;
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
