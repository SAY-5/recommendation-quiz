import { beforeEach, describe, expect, it } from "vitest";
import { clearAnswers, loadAnswers, saveAnswers } from "../lib/storage";

describe("storage", () => {
  beforeEach(() => {
    if (typeof window.localStorage?.clear === "function") {
      window.localStorage.clear();
    }
  });

  it("returns an empty object when nothing is stored", () => {
    expect(loadAnswers()).toEqual({});
  });

  it("round-trips answers", () => {
    saveAnswers({ 1: "light", 2: ["fruity", "floral"] });
    expect(loadAnswers()).toEqual({ 1: "light", 2: ["fruity", "floral"] });
  });

  it("recovers from corrupt storage", () => {
    window.localStorage.setItem("recommendation-quiz:answers/v1", "not json");
    expect(loadAnswers()).toEqual({});
  });

  it("clearAnswers wipes storage", () => {
    saveAnswers({ 1: "x" });
    clearAnswers();
    expect(loadAnswers()).toEqual({});
  });
});
