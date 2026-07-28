/**
 * Records which kernels already existed before the suite ran.
 *
 * `global-teardown.ts` uses this baseline so its kernel sweep only reaps what
 * the run created. Without it, a sweep on a shared or local dev server would
 * kill kernels a developer is actively using.
 */
import {mkdirSync, writeFileSync} from 'node:fs';
import {dirname} from 'node:path';

import {BASELINE_PATH, createApiContext, listKernelIds} from './helpers/session';

export default async function globalSetup(): Promise<void> {
  let kernelIds: string[] = [];
  const api = await createApiContext();
  try {
    kernelIds = await listKernelIds(api);
  } catch (error) {
    // A server that isn't up yet is the tests' problem to report, not setup's.
    console.warn('[e2e setup] could not read pre-existing kernels:', error);
  } finally {
    await api.dispose();
  }

  mkdirSync(dirname(BASELINE_PATH), {recursive: true});
  writeFileSync(BASELINE_PATH, JSON.stringify({kernelIds}, null, 2));
  console.log(`[e2e setup] ${kernelIds.length} pre-existing kernel(s) recorded; they will be left alone.`);
}
