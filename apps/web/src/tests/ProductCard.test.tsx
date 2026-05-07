import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ProductCard } from "../components/ProductCard";

function setViewport(width: number) {
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    writable: true,
    value: width,
  });
  // Mirror the dispatched resize so listeners fire.
  window.dispatchEvent(new Event("resize"));
}

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

describe("ProductCard breakdown", () => {
  beforeEach(() => {
    setViewport(1024);
  });

  afterEach(() => {
    setViewport(1024);
    vi.restoreAllMocks();
  });

  const breakdown = [
    {
      question_id: 10,
      question_prompt: "Which roast?",
      user_answer: "light",
      contribution_pts: 2.0,
      max_contribution_pts: 2.0,
      why: "full match on roast level",
    },
    {
      question_id: 11,
      question_prompt: "Which flavors?",
      user_answer: ["fruity", "floral"],
      contribution_pts: 1.0,
      max_contribution_pts: 2.0,
      why: "partial match on flavor profile (1.0/2.0)",
    },
    {
      question_id: 12,
      question_prompt: "How do you brew?",
      user_answer: "drip",
      contribution_pts: 0.0,
      max_contribution_pts: 3.0,
      why: "no match on brew method",
    },
  ];

  it("renders a row for every question in the breakdown including zero contributions", () => {
    render(
      <ProductCard
        recommendation={{
          product: { id: 4, name: "X", brand: "Y", price_cents: 1500, image_url: "" },
          score: 3.0,
          reasons: [],
          breakdown,
        }}
        rank={1}
      />,
    );
    // Desktop default → already expanded.
    expect(screen.getByTestId("breakdown-row-10")).toBeInTheDocument();
    expect(screen.getByTestId("breakdown-row-11")).toBeInTheDocument();
    expect(screen.getByTestId("breakdown-row-12")).toBeInTheDocument();
    expect(screen.getByText("Which roast?")).toBeInTheDocument();
    expect(screen.getByText(/no match on brew method/i)).toBeInTheDocument();
  });

  it("renders a progressbar per row with matching aria attributes", () => {
    render(
      <ProductCard
        recommendation={{
          product: { id: 5, name: "X", brand: "Y", price_cents: 1000, image_url: "" },
          score: 3.0,
          reasons: [],
          breakdown,
        }}
        rank={1}
      />,
    );
    const bars = screen.getAllByRole("progressbar");
    expect(bars).toHaveLength(3);
    // First row: full match.
    expect(bars[0]).toHaveAttribute("aria-valuenow", "2");
    expect(bars[0]).toHaveAttribute("aria-valuemax", "2");
  });

  it("toggles open and closed on the user click", () => {
    setViewport(360);
    render(
      <ProductCard
        recommendation={{
          product: { id: 9, name: "X", brand: "Y", price_cents: 1000, image_url: "" },
          score: 1.0,
          reasons: [],
          breakdown,
        }}
        rank={1}
      />,
    );
    expect(screen.queryByTestId("breakdown-row-10")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /show why this match/i }));
    expect(screen.getByTestId("breakdown-row-10")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /hide why this match/i }));
    expect(screen.queryByTestId("breakdown-row-10")).not.toBeInTheDocument();
  });

  it("starts collapsed on a mobile viewport (< 640px)", () => {
    setViewport(360);
    render(
      <ProductCard
        recommendation={{
          product: { id: 6, name: "X", brand: "Y", price_cents: 1000, image_url: "" },
          score: 1.0,
          reasons: [],
          breakdown,
        }}
        rank={1}
      />,
    );
    // The toggle button is present, the breakdown rows are not.
    expect(screen.getByRole("button", { name: /show why this match/i })).toBeInTheDocument();
    expect(screen.queryByTestId("breakdown-row-10")).not.toBeInTheDocument();
  });

  it("starts expanded on a desktop viewport (>= 640px)", () => {
    setViewport(1024);
    render(
      <ProductCard
        recommendation={{
          product: { id: 7, name: "X", brand: "Y", price_cents: 1000, image_url: "" },
          score: 1.0,
          reasons: [],
          breakdown,
        }}
        rank={1}
      />,
    );
    // Auto-open on desktop — all rows visible without clicking the toggle.
    expect(screen.getByTestId("breakdown-row-10")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /hide why this match/i })).toBeInTheDocument();
  });

  it("does not render the breakdown UI when no breakdown is provided", () => {
    render(
      <ProductCard
        recommendation={{
          product: { id: 8, name: "X", brand: "Y", price_cents: 1000, image_url: "" },
          score: 0.5,
          reasons: ["matches your roast level"],
        }}
        rank={1}
      />,
    );
    expect(screen.queryByRole("button", { name: /why this match/i })).not.toBeInTheDocument();
  });
});
