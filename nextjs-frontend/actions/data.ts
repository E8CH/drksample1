"use server";
import { cookies } from "next/headers";

export async function generateData(): Promise<{ success: boolean; error?: string }> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { success: false, error: "unauthorized" };

  const res = await fetch(`${process.env.API_URL}/data/generate`, {
    method: "POST",
    headers: { Cookie: `access_token=${token}` },
    cache: "no-store",
  });

  if (res.status === 409) return { success: false, error: "already_running" };
  if (res.status === 401) return { success: false, error: "unauthorized" };
  if (!res.ok) return { success: false, error: "failed" };
  return { success: true };
}

export async function checkGenerationStatus(): Promise<{ status: "running" | "idle" }> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { status: "idle" };

  try {
    const res = await fetch(`${process.env.API_URL}/data/status`, {
      headers: { Cookie: `access_token=${token}` },
      cache: "no-store",
    });
    if (!res.ok) return { status: "idle" };
    return res.json();
  } catch {
    return { status: "idle" };
  }
}

export async function deleteAllData(): Promise<{ success: boolean; error?: string }> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return { success: false, error: "unauthorized" };

  const res = await fetch(`${process.env.API_URL}/data/all`, {
    method: "DELETE",
    headers: { Cookie: `access_token=${token}` },
    cache: "no-store",
  });

  if (res.status === 401) return { success: false, error: "unauthorized" };
  if (!res.ok) return { success: false, error: "failed" };
  return { success: true };
}
