/**
 * Shared helpers for creating and reaping Beaker sessions from e2e tests.
 *
 * Every session these tests create is named with `E2E_SESSION_PREFIX` so that
 * `global-teardown.ts` can identify and sweep them without touching sessions a
 * developer happens to have open against the same server.
 *
 * Cleanup deliberately goes through a standalone `APIRequestContext` rather
 * than `page.request`: teardown most needs to run when a test has timed out or
 * a worker is shutting down, and in those cases the page may already be gone.
 */
import {join} from 'node:path';

import {request as playwrightRequest, type APIRequestContext} from '@playwright/test';

export const E2E_SESSION_PREFIX = 'beaker-e2e';

/**
 * Where global setup stashes the pre-run kernel list for global teardown to
 * read. Both hooks run from the config directory, so a relative path is stable
 * across the two.
 */
export const BASELINE_PATH = join('test-results', 'e2e-kernel-baseline.json');

export type SessionModel = {
  id: string;
  path?: string;
  name?: string;
  kernel?: {id: string} | null;
};

/**
 * The specs address the server by absolute URL rather than via the config's
 * `baseURL`, so resolution lives here to keep the two in agreement.
 */
export function resolveBaseUrl(): string {
  return process.env.BEAKER_E2E_URL ?? 'http://localhost:8888';
}

export function e2eSessionName(suffix: string): string {
  return `${E2E_SESSION_PREFIX}-${suffix}`;
}

export function isE2ESession(session: SessionModel): boolean {
  return [session.path, session.name].some((value) => value?.startsWith(E2E_SESSION_PREFIX));
}

/** Set E2E_CLEANUP_DEBUG=1 to trace what cleanup sends and what comes back. */
const DEBUG = Boolean(process.env.E2E_CLEANUP_DEBUG);

function debug(message: string): void {
  if (DEBUG) console.log(`[e2e cleanup] ${message}`);
}

/**
 * Every `/api/*` call needs `Authorization: token ...`; a cookie-only request
 * is 403 even for GET. The app bootstraps that token from an unauthenticated
 * `GET /config` (see ConfigHandler in src/beaker_notebook/app/handlers.py), and
 * that is where we get it too, so cleanup needs no configuration to work.
 * BEAKER_E2E_TOKEN overrides it for servers where /config isn't reachable.
 */
async function resolveToken(): Promise<string | null> {
  if (process.env.BEAKER_E2E_TOKEN) return process.env.BEAKER_E2E_TOKEN;

  const bootstrap = await playwrightRequest.newContext({baseURL: resolveBaseUrl()});
  try {
    const response = await bootstrap.get('/config');
    if (!response.ok()) {
      console.warn(`[e2e cleanup] GET /config -> ${response.status()}; requests will be unauthenticated.`);
      return null;
    }
    const {token} = (await response.json()) as {token?: string};
    debug(`resolved token from /config: ${token ? `${token.slice(0, 8)}...` : '(empty)'}`);
    return token ?? null;
  } catch (error) {
    console.warn('[e2e cleanup] could not read /config:', error);
    return null;
  } finally {
    await bootstrap.dispose();
  }
}

export async function createApiContext(): Promise<APIRequestContext> {
  const token = await resolveToken();
  return playwrightRequest.newContext({
    baseURL: resolveBaseUrl(),
    extraHTTPHeaders: token ? {Authorization: `token ${token}`} : {},
  });
}

/**
 * Jupyter's Tornado handlers reject non-GET requests without an XSRF token, and
 * the cookie alone is not enough -- it has to be echoed back as a header.
 * `/config` is what seeds that cookie on a fresh context; `/` would too, but it
 * 302s to a generated `?session=<uuid>` on the way.
 */
export async function xsrfHeaders(api: APIRequestContext): Promise<Record<string, string>> {
  await api.get('/config');
  const {cookies} = await api.storageState();
  const xsrf = cookies.find((cookie) => cookie.name === '_xsrf');
  debug(`xsrf cookie ${xsrf ? 'found' : 'MISSING'}`);
  return xsrf ? {'X-XSRFToken': xsrf.value} : {};
}

export async function listSessions(api: APIRequestContext): Promise<SessionModel[]> {
  const response = await api.get('/api/sessions');
  if (!response.ok()) return [];
  return (await response.json()) as SessionModel[];
}

export async function listKernelIds(api: APIRequestContext): Promise<string[]> {
  const response = await api.get('/api/kernels');
  if (!response.ok()) return [];
  const kernels = (await response.json()) as {id: string}[];
  return kernels.map((kernel) => kernel.id);
}

/**
 * Deleting a Beaker session shuts down its kernel, which in turn shuts down the
 * subkernel it spawned -- so sessions are the right granularity to reap at.
 * Returns the ids actually deleted.
 */
export async function deleteSessions(
  api: APIRequestContext,
  matches: (session: SessionModel) => boolean,
): Promise<string[]> {
  const headers = await xsrfHeaders(api);
  const deleted: string[] = [];
  for (const session of (await listSessions(api)).filter(matches)) {
    const response = await api.delete(`/api/sessions/${session.id}`, {headers});
    debug(`DELETE /api/sessions/${session.id} (path=${session.path}) -> ${response.status()}`);
    // 404 means something else already reaped it, which is a fine outcome here.
    if (response.ok() || response.status() === 404) {
      deleted.push(session.id);
    } else {
      console.warn(
        `[e2e cleanup] DELETE session ${session.id} -> ${response.status()} ` +
          `${(await response.text()).slice(0, 200)}`,
      );
    }
  }
  return deleted;
}

export async function deleteKernels(api: APIRequestContext, kernelIds: string[]): Promise<string[]> {
  const headers = await xsrfHeaders(api);
  const deleted: string[] = [];
  for (const kernelId of kernelIds) {
    const response = await api.delete(`/api/kernels/${kernelId}`, {headers});
    debug(`DELETE /api/kernels/${kernelId} -> ${response.status()}`);
    if (response.ok() || response.status() === 404) {
      deleted.push(kernelId);
    } else {
      console.warn(
        `[e2e cleanup] DELETE kernel ${kernelId} -> ${response.status()} ` +
          `${(await response.text()).slice(0, 200)}`,
      );
    }
  }
  return deleted;
}

/** Reap every session this suite created that still matches `name`. */
export async function deleteSessionByName(name: string): Promise<void> {
  const api = await createApiContext();
  try {
    await deleteSessions(api, (session) => session.path === name || session.name === name);
  } catch (error) {
    // Cleanup failure must never be the reason a run reports red.
    console.warn(`[e2e cleanup] failed to delete session '${name}':`, error);
  } finally {
    await api.dispose();
  }
}
