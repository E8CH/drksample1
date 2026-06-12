"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { loginSchema } from "@/lib/definitions";

const ACCESS_TOKEN_MAX_AGE = 3600;

export async function login(prevState: unknown, formData: FormData) {
  const validatedFields = loginSchema.safeParse({
    username: formData.get("username") as string,
    password: formData.get("password") as string,
  });

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  const { username, password } = validatedFields.data;

  let token: string | null = null;
  try {
    const res = await fetch(
      `${process.env.API_URL}/auth/login`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      }
    );

    if (res.status === 401) {
      return { server_validation_error: "로그인 정보가 올바르지 않습니다" };
    }
    if (!res.ok) {
      return { server_error: "서버 오류가 발생했습니다. 다시 시도해주세요." };
    }
    const data = await res.json();
    token = data.access_token;
  } catch {
    return { server_error: "서버에 연결할 수 없습니다." };
  }

  if (token) {
    const cookieStore = await cookies();
    cookieStore.set("access_token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: ACCESS_TOKEN_MAX_AGE,
      path: "/",
    });
    redirect("/dashboard/simulation");
  }
}
