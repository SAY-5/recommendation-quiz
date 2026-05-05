/**
 * Typed client for the recommendation quiz REST API.
 */

export type QuestionKind = "single" | "multi" | "range";

export interface AnswerOption {
  value: string;
  label: string;
  order: number;
}

export interface Question {
  id: number;
  slug: string;
  prompt: string;
  order: number;
  kind: QuestionKind;
  options: AnswerOption[];
}

export interface ProductBrief {
  id: number;
  name: string;
  brand: string;
  price_cents: number;
  image_url: string;
}

export interface Recommendation {
  product: ProductBrief;
  score: number;
  reasons: string[];
}

export interface ScoreResponse {
  recommendations: Recommendation[];
}

export interface ErrorEnvelope {
  code: string;
  message: string;
  retryable: boolean;
  request_id: string | null;
}

export type AnswerValue = string | number | boolean | string[] | null;

export interface AnswerInput {
  question_id: number;
  value: AnswerValue;
}

const DEFAULT_BASE_URL = "http://localhost:8000";

function getBaseUrl(): string {
  const envBase = import.meta.env.VITE_API_BASE_URL;
  return typeof envBase === "string" && envBase.length > 0 ? envBase : DEFAULT_BASE_URL;
}

export class ApiError extends Error {
  constructor(
    public envelope: ErrorEnvelope,
    public status: number,
  ) {
    super(envelope.message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let envelope: ErrorEnvelope;
    try {
      envelope = (await response.json()) as ErrorEnvelope;
    } catch {
      envelope = {
        code: "network_error",
        message: response.statusText || "Request failed",
        retryable: response.status >= 500,
        request_id: null,
      };
    }
    throw new ApiError(envelope, response.status);
  }

  return (await response.json()) as T;
}

export function fetchQuestions(): Promise<Question[]> {
  return request<Question[]>("/api/quiz/questions");
}

export function scoreAnswers(answers: AnswerInput[]): Promise<ScoreResponse> {
  return request<ScoreResponse>("/api/quiz/score", {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}
