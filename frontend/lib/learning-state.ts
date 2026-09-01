export const LEARNING_SECTIONS = ["今日", "沉浸", "复习", "词库", "我"] as const;

export type LearningSection = (typeof LEARNING_SECTIONS)[number];

export type LearningState = {
  active: LearningSection;
  dark: boolean;
  dictation: string;
  writingDraft: string;
};

const STORAGE_KEY = "varbaia:learning-state:v1";

export function decodeLearningState(value: string | null): Partial<LearningState> {
  if (!value) return {};
  try {
    const parsed: unknown = JSON.parse(value);
    if (!parsed || typeof parsed !== "object") return {};
    const state = parsed as Record<string, unknown>;
    return {
      active: LEARNING_SECTIONS.includes(state.active as LearningSection)
        ? (state.active as LearningSection)
        : undefined,
      dark: typeof state.dark === "boolean" ? state.dark : undefined,
      dictation: typeof state.dictation === "string" ? state.dictation : undefined,
      writingDraft: typeof state.writingDraft === "string" ? state.writingDraft : undefined,
    };
  } catch {
    return {};
  }
}

export function saveLearningState(storage: Storage, state: LearningState): void {
  storage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function loadLearningState(storage: Storage): Partial<LearningState> {
  return decodeLearningState(storage.getItem(STORAGE_KEY));
}
