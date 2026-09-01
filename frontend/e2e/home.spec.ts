import { expect, test } from "@playwright/test";

const emptyJson = { contentType: "application/json" };

async function mockOwnerApi(page: import("@playwright/test").Page) {
  await page.addInitScript(() => window.localStorage.setItem("varbaia_access_token", "mock-token"));
  await page.route("http://localhost:8000/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    const reply = (body: object) => route.fulfill({ ...emptyJson, body: JSON.stringify(body) });

    if (path.endsWith("/owner/immersion/imports") && method === "GET") return reply([]);
    if (path.endsWith("/owner/vocabulary/items") && method === "GET") return reply([]);
    if (path.endsWith("/owner/memory") && method === "GET") return reply([]);
    if (path.endsWith("/owner/dictation/attempts") && method === "POST") {
      return reply({ score: 100, missed_words: [], normalized_answer: "The best way to learn is to stay curious." });
    }
    if (path.endsWith("/owner/writing/attempts") && method === "POST") {
      return reply({
        id: "writing-1", prompt: "prompt", draft: "A saved writing response.", clarity_score: 88,
        evaluation_status: "complete", evaluation_error: null,
        feedback: { grammar_score: 86, vocabulary_score: 84, coherence_score: 87, task_completion_score: 89, corrected_draft: "A polished writing response.", suggestions: ["Add one concrete example."], key_errors: [], better_expressions: ["make the city more liveable"] },
      });
    }
    if (path.endsWith("/owner/role-play/sessions") && method === "POST") {
      return reply({ id: "role-1", scenario: "Ordering coffee at a busy cafe", status: "active", messages: [], feedback: null });
    }
    if (path.endsWith("/role-1/turns") && method === "POST") {
      return reply({ id: "role-1", scenario: "Ordering coffee at a busy cafe", status: "active", messages: [{ id: "message-1", speaker: "learner", content: "Could I have a latte, please?", coaching_tip: null, audio_available: false }], feedback: null });
    }
    if (path.endsWith("/role-1/complete") && method === "POST") {
      return reply({ id: "role-1", scenario: "Ordering coffee at a busy cafe", status: "complete", messages: [], feedback: { task_completion: 90, grammar: 85, vocabulary: 82, fluency: 80, pronunciation: null, naturalness: 88, key_corrections: ["Use 'a latte'."], better_expressions: ["Could I get a latte, please?"] } });
    }
    return route.fulfill({ status: 404, ...emptyJson, body: JSON.stringify({ detail: `Unexpected mock request: ${method} ${path}` }) });
  });
}

test("desktop home supports navigation and theme", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "今天，学一点真英语。" })).toBeVisible();
  await page.getByRole("button", { name: "切换明暗主题" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "词库" }).first().click();
  await expect(page.getByRole("heading", { name: "词库" })).toBeVisible();
});

test("mobile home opens and closes navigation without horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 760 });
  await page.goto("/");
  await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
  await page.getByRole("button", { name: "关闭导航" }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test("owner completes dictation, writing, and role-play feedback through mock providers", async ({ page }) => {
  await mockOwnerApi(page);
  await page.goto("/");

  await page.getByLabel("听到什么？").fill("The best way to learn is to stay curious.");
  await page.getByRole("button", { name: "检查" }).click();
  await expect(page.getByText("得分 100 分，完全正确！")).toBeVisible();

  await page.getByRole("button", { name: /写作反馈/ }).click();
  await page.getByLabel("你的回答").fill("A saved writing response.");
  await page.getByRole("button", { name: "获取反馈" }).click();
  await expect(page.getByText("清晰度 88 分")).toBeVisible();
  await page.getByRole("button", { name: "关闭", exact: true }).click();

  await page.getByRole("button", { name: /角色扮演/ }).click();
  await page.getByLabel("文本 fallback").fill("Could I have a latte, please?");
  await page.getByRole("button", { name: "发送文本" }).click();
  await page.getByRole("button", { name: "结束并获取反馈" }).click();
  await expect(page.getByRole("heading", { name: "本轮反馈" })).toBeVisible();
  await expect(page.getByText("完成度 90")).toBeVisible();
  await expect(page.getByText("Could I get a latte, please?")).toBeVisible();
});
