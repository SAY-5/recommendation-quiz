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

  it("renders every reason in the list", () => {
    const reasons = [
      "matches your roast level",
      "matches your flavor profile",
      "matches your brew method",
    ];
    render(
      <ProductCard
        recommendation={{
          product: {
            id: 9,
            name: "Sumatra",
            brand: "Volcanic",
            price_cents: 1800,
            image_url: "",
          },
          score: 7.0,
          reasons,
        }}
        rank={2}
      />,
    );
    for (const r of reasons) {
      expect(screen.getByText(r)).toBeInTheDocument();
    }
  });

  it("renders the image with srcset when image_url is supplied", () => {
    const url = "https://example.com/coffee.jpg";
    const { container } = render(
      <ProductCard
        recommendation={{
          product: { id: 3, name: "X", brand: "Y", price_cents: 1500, image_url: url },
          score: 2.5,
          reasons: [],
        }}
        rank={1}
      />,
    );
    const img = container.querySelector("img");
    expect(img).not.toBeNull();
    expect(img?.getAttribute("src")).toBe(url);
    expect(img?.getAttribute("srcset")).toContain(url);
  });
});
