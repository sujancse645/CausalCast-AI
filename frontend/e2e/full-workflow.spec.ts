import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "node:fs";

test.describe("Phase C: E2E Full Workflow", () => {
  test.setTimeout(90000);

  test("executes primary data to forecast pipeline", async ({ page }) => {
    const tenantId = `e2e-tenant-${Date.now()}`;
    await page.setExtraHTTPHeaders({
      "x-tenant-id": tenantId,
      Authorization: "Bearer test-token",
    });

    await page.goto("/data-intelligence");
    await expect(
      page.getByRole("heading", { name: "Data Intelligence" }).first(),
    ).toBeVisible();

    const originalFixturePath = path.resolve(
      __dirname,
      "../../tests/fixtures/marketing_e2e_fixture.csv",
    );
    const uniqueFixturePath = path.resolve(
      __dirname,
      `../../tests/fixtures/marketing_e2e_fixture_${Date.now()}.csv`,
    );
    const content = fs.readFileSync(originalFixturePath, "utf8");
    const uniqueRow = `2025-04-30,Campaign_${Date.now()},Search,100,1000,10,1,100,0`;
    fs.writeFileSync(uniqueFixturePath, content.trim() + `\n${uniqueRow}\n`);
    const uploadPromise = page.waitForResponse(
      (response) =>
        response.url().includes("/api/v1/datasets/upload") && response.ok(),
    );

    // Provide file to the dropzone input
    await page.locator('input[type="file"]').setInputFiles(uniqueFixturePath);

    // Click Upload button!
    await page.getByRole("button", { name: /Upload dataset/i }).click();

    // Wait for upload to complete
    const uploadResponse = await uploadPromise;
    const uploadData = await uploadResponse.json();
    const datasetId = uploadData.id;
    expect(datasetId).toBeDefined();

    await expect(
      page.getByText(/marketing_e2e_fixture_.*\.csv/).first(),
    ).toBeVisible();

    // ---------------------------------------------------------
    // C3: Schema Inference & Confirmation
    // ---------------------------------------------------------
    await page.goto(`/data-intelligence/${datasetId}/schema`);

    const inferPromise = page.waitForResponse(
      (res) =>
        res.url().includes("/schema/infer") &&
        res.ok() &&
        res.request().method() === "POST",
    );
    await page.getByRole("button", { name: /Run inference/i }).click();
    await inferPromise;

    await expect(
      page.getByRole("button", { name: /Confirm mapping/i }).first(),
    ).toBeVisible({ timeout: 15000 });
    await page
      .getByRole("button", { name: /Confirm mapping/i })
      .first()
      .click();

    const confirmPromise = page.waitForResponse(
      (res) => res.url().includes("/schema/confirm") && res.ok(),
    );
    await page.getByRole("button", { name: "Confirm", exact: true }).click();
    await confirmPromise;

    // ---------------------------------------------------------
    // C4: Data Quality
    // ---------------------------------------------------------
    await page.goto(`/data-intelligence/${datasetId}/quality`);
    await expect(
      page.getByRole("button", { name: /Run analysis/i }).first(),
    ).toBeVisible();

    const evalPromise = page.waitForResponse(
      (res) => res.url().includes("/quality/analyze") && res.ok(),
    );
    await page
      .getByRole("button", { name: /Run analysis/i })
      .first()
      .click();
    await evalPromise;

    await expect(
      page.getByText(/Evaluation Results|findings/i).first(),
    ).toBeVisible();

    // ---------------------------------------------------------
    // C5: Preprocessing
    // ---------------------------------------------------------
    await page.goto(`/data-intelligence/${datasetId}/prepare`);

    // Ensure Target and Date are selected
    await page
      .getByRole("combobox", { name: "Target" })
      .selectOption({ index: 1 });
    await page
      .getByRole("combobox", { name: "Date" })
      .selectOption({ index: 1 });

    // Fill quality override if present
    const overrideCheckbox = page.getByRole("checkbox", {
      name: /Override conditional quality/i,
    });
    if (
      await overrideCheckbox.isVisible({ timeout: 2000 }).catch(() => false)
    ) {
      await overrideCheckbox.check();
      await page
        .getByPlaceholder(/Reason for override/i)
        .fill("E2E Test Override");
    }

    const preparePromise = page.waitForResponse(
      (res) =>
        res.url().includes("/preparations") &&
        res.ok() &&
        res.request().method() === "POST",
    );
    await page
      .getByRole("button", { name: /Start preparation/i })
      .first()
      .click();

    const prepareResponse = await preparePromise;
    const prepareData = await prepareResponse.json();
    const preparedId = prepareData.id;

    // ---------------------------------------------------------
    // C6: Training (Baseline & Advanced)
    // ---------------------------------------------------------
    await page.goto(
      `/data-intelligence/${datasetId}/preparations/${preparedId}/forecast`,
    );

    // Wait for the page to load and model definitions to be fetched
    await expect(
      page.getByRole("heading", { name: "Governed source" }).first(),
    ).toBeVisible({ timeout: 10000 });

    // Trigger the experiment
    const experimentPromise = page.waitForResponse(
      (res) =>
        res.url().includes("/experiments") &&
        res.ok() &&
        res.request().method() === "POST",
      { timeout: 60000 },
    );
    await page
      .getByRole("button", { name: /Run baseline and advanced experiment/i })
      .click();

    const experimentResponse = await experimentPromise;
    const experimentData = await experimentResponse.json();
    const experimentId = experimentData.id;
    expect(experimentId).toBeDefined();

    // ---------------------------------------------------------
    // C7: Explainability
    // ---------------------------------------------------------
    await page.goto(`/explainability`);
    await expect(
      page.getByRole("heading", { name: "Explainability" }).first(),
    ).toBeVisible();

    // ---------------------------------------------------------
    // C8: Business Intelligence
    // ---------------------------------------------------------
    await page.goto(`/analytics/operations`);
    await expect(
      page.getByRole("heading", { name: "Operations Analytics" }).first(),
    ).toBeVisible();

    // ---------------------------------------------------------
    // C9: AI Copilot
    // ---------------------------------------------------------
    await page.goto(`/copilot`);
    await expect(
      page.getByRole("heading", { name: "AI Copilot" }).first(),
    ).toBeVisible();
  });
});
