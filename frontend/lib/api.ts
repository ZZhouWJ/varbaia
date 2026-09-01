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

export type ImportJob = { id: string; status: string; progress: number; message: string; media_asset_id: string | null };
export type ImportEvent = { status: string; progress: number; message: string; created_at: string };
export type TranscriptSegment = { id: string; start_ms: number; end_ms: number; text: string; translation: string | null; order: number };

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

export async function getMediaObjectUrl(assetId: string): Promise<string> {
  const response = await ownerFetch(`/owner/immersion/media/${assetId}`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取视频失败");
  return URL.createObjectURL(await response.blob());
}

export async function getTranscript(jobId: string): Promise<TranscriptSegment[]> {
  const response = await ownerFetch(`/owner/immersion/imports/${jobId}/transcript`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取字幕失败");
  return response.json();
}

export async function saveVideoProgress(jobId: string, positionSeconds: number, durationSeconds: number): Promise<void> {
  const response = await ownerFetch("/owner/progress", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resource_type: "immersion_video", resource_id: jobId, last_position_seconds: Math.max(0, Math.round(positionSeconds)), completion_percent: durationSeconds > 0 ? Math.min(100, Math.round(positionSeconds / durationSeconds * 100)) : 0 }),
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "保存学习进度失败");
}

export type DictationResult = { score: number; missed_words: string[]; normalized_answer: string };
export type VocabularyItem = { id: string; term: string; definition: string; interval_days: number; ease: number; repetitions: number; next_review_at: string };
export type PronunciationResult = {
  overall_score: number | null;
  pronunciation_accuracy: number | null;
  pronunciation_fluency: number | null;
  pronunciation_completion: number | null;
  word_results: Array<{ text: string | null; start_time_ms: number | null; end_time_ms: number | null; pronunciation_accuracy: number | null; pronunciation_fluency: number | null; match_tag: number | null }>;
  phone_results: Array<{ text: string | null; start_time_ms: number | null; end_time_ms: number | null; pronunciation_accuracy: number | null; match_tag: number | null }>;
};
export type PronunciationAttempt = { id: string; reference_text: string; evaluation_status: string; result: PronunciationResult | null; evaluation_error: string | null };
export type LearnerMemoryItem = { id: string; category: "pronunciation" | "listening" | "vocabulary" | "grammar" | "fluency" | "writing"; title: string; detail: string; source_type: string; occurrence_count: number; severity: number; status: string; last_seen_at: string };
export type RolePlaySession = {
  id: string;
  scenario: string;
  status: string;
  messages: Array<{ id: string; speaker: string; content: string; coaching_tip: string | null; audio_available: boolean }>;
  feedback: {
    task_completion: number;
    grammar: number;
    vocabulary: number;
    fluency: number | null;
    pronunciation: number | null;
    naturalness: number;
    key_corrections: string[];
    better_expressions: string[];
  } | null;
};
export type WritingAttempt = {
  id: string;
  prompt: string;
  draft: string;
  clarity_score: number | null;
  evaluation_status: string;
  feedback: { corrected_draft?: string; suggestions?: string[]; grammar_score?: number | null; vocabulary_score?: number | null; coherence_score?: number | null; task_completion_score?: number | null; key_errors?: string[]; better_expressions?: string[] } | null;
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

export async function completeRolePlaySession(sessionId: string): Promise<RolePlaySession> {
  const response = await ownerFetch(`/owner/role-play/sessions/${sessionId}/complete`, {
    method: "POST",
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "无法生成角色扮演反馈");
  return response.json();
}

export async function submitRolePlayVoiceTurn(sessionId: string, audio: Blob): Promise<RolePlaySession> {
  const body = new FormData();
  body.append("audio", audio, "role-play.webm");
  const response = await ownerFetch(`/owner/role-play/sessions/${sessionId}/voice-turns`, { method: "POST", body });
  if (!response.ok) throw new Error((await response.json()).detail ?? "语音角色扮演提交失败");
  return response.json();
}

export async function getRolePlayAudioUrl(sessionId: string, messageId: string): Promise<string> {
  const response = await ownerFetch(`/owner/role-play/sessions/${sessionId}/messages/${messageId}/audio`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取角色扮演语音失败");
  return URL.createObjectURL(await response.blob());
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

export async function listVocabularyItems(): Promise<VocabularyItem[]> {
  const response = await ownerFetch("/owner/vocabulary/items");
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取词库失败");
  return response.json();
}

export async function listLearnerMemory(): Promise<LearnerMemoryItem[]> {
  const response = await ownerFetch("/owner/memory");
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取学习记忆失败");
  return response.json();
}

export async function markLearnerMemoryMastered(memoryId: string): Promise<LearnerMemoryItem> {
  const response = await ownerFetch(`/owner/memory/${memoryId}/master`, { method: "POST" });
  if (!response.ok) throw new Error((await response.json()).detail ?? "更新学习记忆失败");
  return response.json();
}

export async function deleteLearnerMemory(memoryId: string): Promise<void> {
  const response = await ownerFetch(`/owner/memory/${memoryId}`, { method: "DELETE" });
  if (!response.ok) throw new Error((await response.json()).detail ?? "删除学习记忆失败");
}

export async function reviewVocabulary(itemId: string, grade: "again" | "hard" | "good" | "easy"): Promise<VocabularyItem> {
  const response = await ownerFetch(`/owner/vocabulary/items/${itemId}/review/${grade}`, { method: "POST" });
  if (!response.ok) throw new Error((await response.json()).detail ?? "保存复习结果失败");
  return response.json();
}

export async function submitPronunciation(referenceText: string, audio: Blob): Promise<PronunciationAttempt> {
  const body = new FormData();
  body.append("reference_text", referenceText);
  body.append("audio", audio, "shadowing.webm");
  const response = await ownerFetch("/owner/pronunciation/attempts", { method: "POST", body });
  if (!response.ok) throw new Error((await response.json()).detail ?? "跟读提交失败");
  return response.json();
}

export async function getPronunciationAttempt(attemptId: string): Promise<PronunciationAttempt> {
  const response = await ownerFetch(`/owner/pronunciation/attempts/${attemptId}`);
  if (!response.ok) throw new Error((await response.json()).detail ?? "读取跟读结果失败");
  return response.json();
}
