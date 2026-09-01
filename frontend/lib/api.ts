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

async function refreshAccessToken(): Promise<string | null> {
  const response = await fetch(`${apiBaseUrl}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    clearAccessToken();
    return null;
  }
  const body = await response.json();
  window.localStorage.setItem(tokenKey, body.access_token);
  return body.access_token;
}

export type ImportJob = { id: string; status: string; progress: number; message: string };

async function ownerFetch(path: string, init: RequestInit = {}): Promise<Response> {
  let token = getAccessToken();
  if (!token) throw new Error("请先登录 Owner 账户");
  const request = () => fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${token}` },
  });
  let response = await request();
  if (response.status === 401 && (token = await refreshAccessToken())) response = await request();
  if (response.status === 401) throw new Error("登录已过期，请重新登录");
  return response;
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

export async function uploadMedia(video: File): Promise<ImportJob> {
  const body = new FormData();
  body.append("video", video);
  const response = await ownerFetch("/owner/immersion/uploads", { method: "POST", body });
  if (!response.ok) throw new Error((await response.json()).detail ?? "上传失败");
  return response.json();
}

export async function getImport(jobId: string): Promise<ImportJob> {
  const response = await ownerFetch(`/owner/immersion/imports/${jobId}`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取导入进度失败");
  return response.json();
}

export async function listImports(): Promise<ImportJob[]> {
  const response = await ownerFetch("/owner/immersion/imports");
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取导入列表失败");
  return response.json();
}

export type DictationResult = { score: number; missed_words: string[]; normalized_answer: string };

export async function submitDictation(answer: string, reference: string): Promise<DictationResult> {
  const response = await ownerFetch("/owner/dictation/attempts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer, reference }),
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "听写提交失败");
  return response.json();
}
