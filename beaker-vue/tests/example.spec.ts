import { test as base, expect, type Page } from '@playwright/test';

import { deleteSessionByName, e2eSessionName, resolveBaseUrl } from './helpers/session';

/**
 * One session per test, deleted as soon as the test finishes.
 *
 * Navigating to `/` (as this fixture used to) makes the server redirect to a
 * freshly generated `?session=<uuid>`, so every test already got its own
 * session -- it just had no name the suite could recognise afterwards, so
 * nothing was ever cleaned up. Naming the session ourselves keeps that
 * isolation and makes teardown a direct delete.
 *
 * Sharing one session per worker was tried and does not work: notebook state
 * persists per session, so the second test on a worker inherits the previous
 * test's notebook instead of a fresh one, and the `.code-cell` locators find
 * nothing. Isolation here is load-bearing, not incidental.
 *
 * Deleting the session shuts down its kernel and that kernel's subkernel, so
 * live kernels track the worker count rather than the test count.
 *
 * The name must be unique per *run*, not just per test: notebook state is
 * snapshotted to disk under the session name and outlives the session itself,
 * so a name derived from testId alone would make each run restore the previous
 * run's notebook -- which shows up as cells the test didn't expect.
 */
const test = base.extend<{sessionPage: Page}>(
  {
    sessionPage: async ({page}, use, testInfo) => {
      const sessionName = e2eSessionName(`${testInfo.testId}-${Date.now()}`);
      await page.goto(`${resolveBaseUrl()}/?session=${encodeURIComponent(sessionName)}`);
      await expect(page.locator("span.status-label")).toBeVisible();
      await expect(page.locator("span.status-label")).toHaveText("Ready", {timeout: 45_000});
      await use(page);
      await deleteSessionByName(sessionName);
    }
  }
);

test.describe.configure({ mode: 'parallel' });

test('Agent: Say Hello', async ({ sessionPage }) => {
  await expect(sessionPage.getByPlaceholder("Ask the AI or request an operation.")).toBeVisible();
  await sessionPage.getByPlaceholder("Ask the AI or request an operation.").fill("say hello");
  await sessionPage.getByLabel("Submit").click();
  await expect(sessionPage.getByText("Beaker Agent")).toBeVisible({timeout: 30_000});
  await expect(sessionPage.locator(".agent-cell-content")).toBeVisible();
  await expect(sessionPage.locator(".agent-cell-content")).toContainText("hello", {ignoreCase: true, timeout: 60_000});
});

test('Agent: Run Code', async ({ sessionPage }) => {
  await expect(sessionPage.getByPlaceholder("Ask the AI or request an operation.")).toBeVisible();
  await sessionPage
    .getByPlaceholder("Ask the AI or request an operation.")
    .fill("use the python tool to compute 21 + 115");
  await sessionPage.getByLabel("Submit").click();
  await expect(sessionPage.getByText("Beaker Agent")).toBeVisible({timeout: 30_000});
  await expect(sessionPage.locator(".code-cell")).toBeVisible();
  await expect(sessionPage.locator(".code-cell-output-box")).toContainText(`${21 + 115}`, {timeout: 60_000});
});

test('Code Cell: Execute Python (control+enter)', async ({ sessionPage }) => {
  const codeCell = sessionPage.locator(".beaker-notebook .code-cell .cm-content");
  const testString = "Code Cell Test String"
  await expect(codeCell).toBeVisible();
  await codeCell.click();
  await codeCell.fill(`print("${testString}")`)
  await codeCell.press("Control+Enter")
  // should NOT add new cell
  await expect(sessionPage.locator(".code-cell")).toHaveCount(1);
  await expect(sessionPage.locator(".code-cell-output-box"))
    .toContainText(testString, {timeout: 20_000});
});

test('Code Cell: Execute Python (shift+enter)', async ({ sessionPage }) => {
  const codeCell = sessionPage.locator(".beaker-notebook .code-cell .cm-content");
  const testString = "Code Cell Test String"
  await expect(codeCell).toBeVisible();
  await codeCell.click();
  await codeCell.fill(`print("${testString}")`)
  await codeCell.press("Shift+Enter")
  // should add new cell
  await expect(sessionPage.locator(".code-cell")).toHaveCount(2);
  await expect(sessionPage.locator(".code-cell-output-box"))
    .toContainText(testString, {timeout: 20_000});
});

test('Code Cell: Execute Python (Toolbar Button)', async ({ sessionPage }) => {
  const codeCell = sessionPage.locator(".beaker-notebook .code-cell .cm-content");
  const testString = "Code Cell Test String"
  await expect(codeCell).toBeVisible();
  await codeCell.click();
  await codeCell.fill(`print("${testString}")`)
  await sessionPage.locator(".notebook-toolbar > .p-toolbar-start > button:nth-child(3)").click();
  await expect(sessionPage.locator(".code-cell")).toBeVisible({timeout: 20_000});
  await expect(sessionPage.locator(".code-cell-output-box"))
    .toContainText(testString, {timeout: 20_000});
});

test('File Browser: Show README.md with metadata', async ({ sessionPage }) => {
  const filesTabButton = sessionPage.locator('.sidemenu .left .button-panel > button').nth(1);
  await expect(filesTabButton).toBeVisible();
  await filesTabButton.click();

  const filePanel = sessionPage.locator('.file-container');
  await expect(filePanel).toBeVisible({timeout: 30_000});

  const fileTable = sessionPage.locator('.file-table');
  await expect(fileTable).toBeVisible({timeout: 30_000});

  const readmeRow = fileTable.getByRole('row', { name: /README\.md/ });
  await expect(readmeRow).toBeVisible();

  await expect(readmeRow).toContainText(/\d+\s+(second|minute|hour|day|month|year)s?\s+ago|just now|a (second|minute|hour|day|month|year) ago|last (week|month)/i, {timeout: 5_000});

  await expect(readmeRow).toContainText(/\d+\.?\d*\s?(B|KB|MB|GB)/i);
});
