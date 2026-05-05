import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, fetchQuestions, scoreAnswers } from "../lib/api";

describe("api client", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches questions", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => [{ id: 1, slug: "x", prompt: "x", order: 1, kind: "single", options: [] }],
    });
    const questions = await fetchQuestions();
    expect(questions).toHaveLength(1);
    expect(questions[0]?.slug).toBe("x");
  });

  it("posts answers to /api/quiz/score", async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ recommendations: [] }),
    });
    await scoreAnswers([{ question_id: 1, value: "light" }]);
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/quiz/score"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws ApiError on non-ok response", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: async () => ({
        code: "validation_error",
        message: "answers required",
        retryable: false,
        request_id: "abc",
      }),
    });
    await expect(fetchQuestions()).rejects.toBeInstanceOf(ApiError);
  });
});
