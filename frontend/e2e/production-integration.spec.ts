import { expect, test } from "@playwright/test";

test("runs a real forecast and grounded RAG answer", async ({ page }) => {
  const browserErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") browserErrors.push(message.text());
  });

  await page.goto("/forecasts");
  await expect(
    page.getByRole("heading", { name: "Production Forecasts" }),
  ).toBeVisible();
  await expect(page.getByText("Model and data contract")).toBeVisible({
    timeout: 30_000,
  });

  await page.getByLabel("Dataset").selectOption("online_retail");
  await expect(page.getByText(/xgboost_model/)).toBeVisible();
  await page.getByLabel("Horizon").fill("2");
  await page.getByRole("button", { name: "Generate forecast" }).click();
  await expect(
    page.getByRole("heading", { name: "Online Retail II result" }),
  ).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText(/Model loaded from disk/)).toBeVisible();

  await page.goto("/copilot");
  const question = page.getByLabel("Ask a question about the project");
  await question.fill("Which model performs best for Tourism Quarterly?");
  await page.getByRole("button", { name: "Ask" }).click();
  await expect(page.getByText(/xgboost has the lowest RMSE/)).toBeVisible({
    timeout: 60_000,
  });
  await expect(
    page.getByText("reports/tourism/model_comparison.json"),
  ).toBeVisible();

  expect(browserErrors).toEqual([]);
});
