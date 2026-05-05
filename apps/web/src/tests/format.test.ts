import { describe, expect, it } from "vitest";
import { formatPrice } from "../lib/format";

describe("formatPrice", () => {
  it("renders cents as a USD-formatted string", () => {
    expect(formatPrice(2400)).toBe("$24.00");
    expect(formatPrice(0)).toBe("$0.00");
    expect(formatPrice(99)).toBe("$0.99");
  });
});
