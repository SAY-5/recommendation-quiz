import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProductCard } from "../components/ProductCard";

describe("ProductCard", () => {
  it("renders brand, name, formatted price, and reasons", () => {
    render(
      <ProductCard
        recommendation={{
          product: {
            id: 1,
            name: "Yirgacheffe",
            brand: "Highland Roasters",
            price_cents: 2400,
            image_url: "",
          },
          score: 5.5,
          reasons: ["matches your roast level", "matches your flavor profile"],
        }}
        rank={1}
      />,
    );
    expect(screen.getByText("Highland Roasters")).toBeInTheDocument();
    expect(screen.getByText("Yirgacheffe")).toBeInTheDocument();
    expect(screen.getByText("$24.00")).toBeInTheDocument();
    expect(screen.getByText("5.50")).toBeInTheDocument();
    expect(screen.getByText("matches your roast level")).toBeInTheDocument();
  });

  it("falls back to a rank badge when no image is provided", () => {
    render(
      <ProductCard
        recommendation={{
          product: { id: 2, name: "X", brand: "Y", price_cents: 1000, image_url: "" },
          score: 1,
          reasons: [],
        }}
        rank={3}
      />,
    );
    expect(screen.getByText("#3")).toBeInTheDocument();
  });
});
