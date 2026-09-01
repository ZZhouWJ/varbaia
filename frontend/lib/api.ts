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

export async function logout(): Promise<void> {
  const token = getAccessToken();
  if (token) {
    await fetch(`${apiBaseUrl}/auth/logout`, {
      method: "POST",
      credentials: "include",
      headers: { Authorization: `Bearer ${token}` },
    });
  }
  clearAccessToken();
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
export type ImportEvent = { status: string; progress: number; message: string; created_at: string };

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

export async function uploadMedia(video: File, subtitle?: File): Promise<ImportJob> {
  const body = new FormData();
  body.append("video", video);
  if (subtitle) body.append("subtitle", subtitle);
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

export async function getImportEvents(jobId: string): Promise<ImportEvent[]> {
  const response = await ownerFetch(`/owner/immersion/imports/${jobId}/events`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取任务事件失败");
  return response.json();
}

export type DictationResult = { score: number; missed_words: string[]; normalized_answer: string };
export type RolePlaySession = { id: string; scenario: string; status: string; messages: Array<{ speaker: string; content: string; coaching_tip: string | null }> };
export type WritingAttempt = {
  id: string;
  prompt: string;
  draft: string;
  clarity_score: number | null;
  evaluation_status: string;
  feedback: { corrected_draft?: string; suggestions?: string[] } | null;
  evaluation_error: string | null;
};

export async function submitDictation(answer: string, reference: string): Promise<DictationResult> {
  const response = await ownerFetch("/owner/dictation/attempts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer, reference }),
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "听写提交失败");
  return response.json();
}

export async function createRolePlaySession(scenario: string): Promise<RolePlaySession> {
  const response = await ownerFetch("/owner/role-play/sessions", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenario }),
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "无法创建角色扮演会话");
  return response.json();
}

export async function submitRolePlayTurn(sessionId: string, learnerMessage: string): Promise<RolePlaySession> {
  const response = await ownerFetch(`/owner/role-play/sessions/${sessionId}/turns`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ learner_message: learnerMessage }),
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "角色扮演提交失败");
  return response.json();
}

export async function getRolePlaySession(sessionId: string): Promise<RolePlaySession> {
  const response = await ownerFetch(`/owner/role-play/sessions/${sessionId}`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取角色扮演会话失败");
  return response.json();
}

export async function submitWriting(prompt: string, content: string): Promise<WritingAttempt> {
  const response = await ownerFetch("/owner/writing/attempts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, draft: content }),
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "写作提交失败");
  return response.json();
}

export async function getWritingAttempt(attemptId: string): Promise<WritingAttempt> {
  const response = await ownerFetch(`/owner/writing/attempts/${attemptId}`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取写作反馈失败");
  return response.json();
}
