export type ReviewGrade = "again" | "hard" | "good" | "easy";

export type ReviewState = {
  intervalDays: number;
  ease: number;
  repetitions: number;
};

export function scheduleReview(current: ReviewState, grade: ReviewGrade): ReviewState {
  if (grade === "again") return { intervalDays: 1, ease: Math.max(1.3, current.ease - 0.2), repetitions: 0 };
  const multiplier = grade === "easy" ? 1.3 : grade === "hard" ? 0.75 : 1;
  const nextEase = grade === "easy" ? current.ease + 0.15 : grade === "hard" ? Math.max(1.3, current.ease - 0.15) : current.ease;
  const base = current.repetitions === 0 ? 1 : current.repetitions === 1 ? 3 : Math.round(current.intervalDays * nextEase);
  return { intervalDays: Math.max(1, Math.round(base * multiplier)), ease: nextEase, repetitions: current.repetitions + 1 };
}
