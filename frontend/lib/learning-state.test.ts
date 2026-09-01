import { describe, expect, it } from "vitest";

import { decodeLearningState, saveLearningState } from "./learning-state";

describe("learning state persistence", () => {
  it("keeps only supported, user-entered state", () => {
    const restored = decodeLearningState(
      JSON.stringify({ active: "沉浸", dark: true, dictation: "hello", writingDraft: "draft" }),
    );

    expect(restored).toEqual({
      active: "沉浸",
      dark: true,
      dictation: "hello",
      writingDraft: "draft",
    });
  });

  it("rejects invalid JSON and unknown navigation entries", () => {
    expect(decodeLearningState("not json")).toEqual({});
    expect(decodeLearningState(JSON.stringify({ active: "社区", dictation: 12 }))).toEqual({
      active: undefined,
      dark: undefined,
      dictation: undefined,
      writingDraft: undefined,
    });
  });

  it("serializes state without retaining media or credentials", () => {
    const values = new Map<string, string>();
    const storage = { setItem: (key: string, value: string) => values.set(key, value) } as Storage;

    saveLearningState(storage, {
      active: "今日",
      dark: false,
      dictation: "I can hear the sentence.",
      writingDraft: "A saved draft.",
    });

    expect([...values.values()][0]).toBe(
      '{"active":"今日","dark":false,"dictation":"I can hear the sentence.","writingDraft":"A saved draft."}',
    );
  });
});
