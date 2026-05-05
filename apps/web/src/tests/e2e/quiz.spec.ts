import { test, expect } from "@playwright/test";

const QUESTIONS = [
  {
    id: 1,
    slug: "roast_preference",
    prompt: "Which roast level do you usually reach for?",
    order: 1,
    kind: "single",
    options: [
      { value: "light", label: "Light", order: 1 },
      { value: "medium", label: "Medium", order: 2 },
      { value: "dark", label: "Dark", order: 3 },
    ],
  },
  {
    id: 2,
    slug: "brew_method",
    prompt: "How do you brew at home?",
    order: 2,
    kind: "single",
    options: [
      { value: "drip", label: "Drip", order: 1 },
      { value: "espresso", label: "Espresso", order: 2 },
    ],
  },
];

const SCORE_RESPONSE = {
  recommendations: [
    {
      product: {
        id: 1,
        name: "Yirgacheffe Single Origin",
        brand: "Highland Roasters",
        price_cents: 2400,
        image_url: "",
      },
      score: 5.0,
      reasons: ["matches your roast level", "matches your brew method"],
    },
    {
      product: {
        id: 2,
        name: "Colombia Supremo",
        brand: "Andes Trade",
        price_cents: 1500,
        image_url: "",
      },
      score: 3.0,
      reasons: ["matches your roast level"],
    },
  ],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/quiz/questions", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(QUESTIONS),
    });
  });
  await page.route("**/api/quiz/score", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(SCORE_RESPONSE),
    });
  });
});

test("user can complete the quiz and see recommendations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /find your next coffee/i })).toBeVisible();

  await page.getByRole("button", { name: /start the quiz/i }).click();

  // Step 1
  await expect(page.getByText(/which roast level/i)).toBeVisible();
  await page.getByLabel("Light").check();
  await page.getByRole("button", { name: /next/i }).click();

  // Step 2 — last
  await expect(page.getByText(/how do you brew at home/i)).toBeVisible();
  await page.getByLabel("Drip").check();
  await page.getByRole("button", { name: /see recommendations/i }).click();

  // Results
  await expect(page.getByRole("heading", { name: /your top picks/i })).toBeVisible();
  await expect(page.getByText("Yirgacheffe Single Origin")).toBeVisible();
  await expect(page.getByText("Colombia Supremo")).toBeVisible();
});

test("back button preserves the previous answer", async ({ page }) => {
  await page.goto("/quiz/1");
  await page.getByLabel("Medium").check();
  await page.getByRole("button", { name: /next/i }).click();
  await page.getByRole("button", { name: /back/i }).click();
  await expect(page.getByLabel("Medium")).toBeChecked();
});
