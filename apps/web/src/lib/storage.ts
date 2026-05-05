import type { AnswerValue } from "./api";

const STORAGE_KEY = "recommendation-quiz:answers/v1";

export type AnswersMap = Record<number, AnswerValue>;

export function loadAnswers(): AnswersMap {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed === "object" && parsed !== null) {
      return parsed as AnswersMap;
    }
    return {};
  } catch {
    return {};
  }
}

export function saveAnswers(answers: AnswersMap): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(answers));
  } catch {
    // Storage may be unavailable (e.g. private mode); ignore.
  }
}

export function clearAnswers(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}
