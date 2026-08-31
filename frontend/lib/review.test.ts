import { describe, expect, it } from "vitest";
import { scheduleReview } from "./review";

describe("scheduleReview", () => {
  it("resets a missed card for tomorrow", () => {
    expect(scheduleReview({ intervalDays: 8, ease: 2.5, repetitions: 3 }, "again")).toEqual({ intervalDays: 1, ease: 2.3, repetitions: 0 });
  });

  it("grows successful reviews without a zero interval", () => {
    const first = scheduleReview({ intervalDays: 0, ease: 2.5, repetitions: 0 }, "good");
    expect(first.intervalDays).toBe(1);
    expect(scheduleReview(first, "easy").intervalDays).toBeGreaterThanOrEqual(3);
  });
});
