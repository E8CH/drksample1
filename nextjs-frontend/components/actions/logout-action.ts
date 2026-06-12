"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export async function logout() {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (token) {
    try {
      await fetch(`${process.env.API_URL}/auth/logout`, {
        method: "POST",
        headers: { Cookie: `access_token=${token}` },
      });
    } catch {
      // 백엔드 오류 무시 — 쿠키는 로컬에서 삭제
    }
  }

  cookieStore.delete("access_token");
  redirect("/login");
}
