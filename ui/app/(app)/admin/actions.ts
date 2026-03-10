"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";

const ADMIN_COOKIE = "xmrcheckout_admin_key";

export type AdminLoginState = {
  error: string | null;
};

export type AdminCreateUserState = {
  error: string | null;
  success: string | null;
  apiKey: string | null;
  webhookSecret: string | null;
  storeId: string | null;
};

export type AdminDeleteUserState = {
  error: string | null;
  success: string | null;
  deletedId: string | null;
};

async function getAdminKey(): Promise<string | null> {
  return (await cookies()).get(ADMIN_COOKIE)?.value ?? null;
}

export async function adminLoginAction(
  _prevState: AdminLoginState,
  formData: FormData
): Promise<AdminLoginState> {
  const key = String(formData.get("admin_key") ?? "").trim();
  if (!key) {
    return { error: "Admin key is required." };
  }

  const response = await fetch(`${apiBaseUrl}/api/admin/auth/verify`, {
    method: "POST",
    headers: { "X-Admin-Key": key },
    cache: "no-store",
  });

  if (!response.ok) {
    return { error: "Invalid admin key." };
  }

  const cookieStore = await cookies();
  cookieStore.set(ADMIN_COOKIE, key, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });

  redirect("/admin");
}

export async function adminLogoutAction() {
  const cookieStore = await cookies();
  cookieStore.set(ADMIN_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  redirect("/admin");
}

export async function adminCreateUserAction(
  _prevState: AdminCreateUserState,
  formData: FormData
): Promise<AdminCreateUserState> {
  const adminKey = await getAdminKey();
  if (!adminKey) {
    return { error: "Not authenticated.", success: null, apiKey: null, webhookSecret: null, storeId: null };
  }

  const paymentAddress = String(formData.get("payment_address") ?? "").trim();
  const viewKey = String(formData.get("view_key") ?? "").trim();

  if (!paymentAddress || !viewKey) {
    return { error: "Address and view key are required.", success: null, apiKey: null, webhookSecret: null, storeId: null };
  }

  const response = await fetch(`${apiBaseUrl}/api/admin/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Key": adminKey,
    },
    body: JSON.stringify({ payment_address: paymentAddress, view_key: viewKey }),
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    const message = detail?.detail ?? "Failed to create user.";
    return { error: message, success: null, apiKey: null, webhookSecret: null, storeId: null };
  }

  const data = (await response.json()) as {
    api_key: string;
    webhook_secret: string;
    store_id: string;
  };

  revalidatePath("/admin");
  return {
    error: null,
    success: `Merchant created.`,
    apiKey: data.api_key,
    webhookSecret: data.webhook_secret,
    storeId: data.store_id,
  };
}

export async function adminDeleteUserAction(
  _prevState: AdminDeleteUserState,
  formData: FormData
): Promise<AdminDeleteUserState> {
  const adminKey = await getAdminKey();
  if (!adminKey) {
    return { error: "Not authenticated.", success: null, deletedId: null };
  }

  const userId = String(formData.get("user_id") ?? "").trim();
  if (!userId) {
    return { error: "User ID missing.", success: null, deletedId: null };
  }

  const response = await fetch(`${apiBaseUrl}/api/admin/users/${encodeURIComponent(userId)}`, {
    method: "DELETE",
    headers: { "X-Admin-Key": adminKey },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    const message = detail?.detail ?? "Failed to delete user.";
    return { error: message, success: null, deletedId: null };
  }

  revalidatePath("/admin");
  return { error: null, success: "Merchant deleted.", deletedId: userId };
}

export type AdminUser = {
  id: string;
  payment_address: string;
  invoice_count: number;
  created_at: string | null;
};

export async function fetchAdminUsers(): Promise<AdminUser[] | null> {
  const adminKey = await getAdminKey();
  if (!adminKey) return null;

  const response = await fetch(`${apiBaseUrl}/api/admin/users`, {
    headers: { "X-Admin-Key": adminKey },
    cache: "no-store",
  });

  if (!response.ok) return null;
  return response.json();
}
