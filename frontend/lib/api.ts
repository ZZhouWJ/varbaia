const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
const tokenKey = "varbaia_access_token";

export function getAccessToken(): string | null {
  return window.localStorage.getItem(tokenKey);
}

export function clearAccessToken(): void {
  window.localStorage.removeItem(tokenKey);
}

export async function login(email: string, password: string): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "登录失败");
  const body = await response.json();
  window.localStorage.setItem(tokenKey, body.access_token);
}

export type ImportJob = { id: string; status: string; progress: number; message: string };

async function ownerFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getAccessToken();
  if (!token) throw new Error("请先登录 Owner 账户");
  return fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${token}` },
  });
}

export async function createUrlImport(sourceUrl: string): Promise<ImportJob> {
  const response = await ownerFetch("/owner/immersion/imports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_url: sourceUrl, accent: "en-US" }),
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "导入失败");
  return response.json();
}

export async function getImport(jobId: string): Promise<ImportJob> {
  const response = await ownerFetch(`/owner/immersion/imports/${jobId}`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取导入进度失败");
  return response.json();
}
