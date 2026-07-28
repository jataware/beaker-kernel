/**
 * Backstop cleanup for the e2e suite.
 *
 * Each test already deletes its own session as it finishes; this exists for the
 * cases that can't cover -- a crashed worker, a killed run, or a session whose
 * kernel outlived its session record.
 *
 * Two passes, in order:
 *   1. Delete every session named with the e2e prefix. Deleting a Beaker
 *      session shuts down its kernel, which shuts down that kernel's subkernel.
 *   2. Delete any kernel that wasn't present before the run and isn't attached
 *      to a surviving session -- i.e. orphans left by a shutdown that didn't
 *      cascade. Kernels recorded by global setup are never touched.
 */
import {readFileSync} from 'node:fs';

import {
  BASELINE_PATH,
  createApiContext,
  deleteKernels,
  deleteSessions,
  isE2ESession,
  listKernelIds,
  listSessions,
} from './helpers/session';

function readBaselineKernelIds(): Set<string> | null {
  try {
    const {kernelIds} = JSON.parse(readFileSync(BASELINE_PATH, 'utf-8')) as {kernelIds: string[]};
    return new Set(kernelIds);
  } catch {
    // No baseline means we can't tell ours from theirs, so the kernel sweep
    // is skipped entirely rather than risking a developer's running kernels.
    return null;
  }
}

export default async function globalTeardown(): Promise<void> {
  const api = await createApiContext();
  try {
    const deletedSessions = await deleteSessions(api, isE2ESession);
    if (deletedSessions.length) {
      console.log(`[e2e teardown] deleted ${deletedSessions.length} leftover session(s).`);
    }

    const baseline = readBaselineKernelIds();
    if (!baseline) {
      console.warn(`[e2e teardown] no baseline at ${BASELINE_PATH}; skipping kernel sweep.`);
      return;
    }

    // Anything still attached to a session is in use by something that isn't us.
    const attached = new Set(
      (await listSessions(api))
        .map((session) => session.kernel?.id)
        .filter((id): id is string => Boolean(id)),
    );
    const orphans = (await listKernelIds(api)).filter(
      (id) => !baseline.has(id) && !attached.has(id),
    );

    if (orphans.length) {
      const deleted = await deleteKernels(api, orphans);
      console.log(`[e2e teardown] deleted ${deleted.length} orphaned kernel(s).`);
    }
  } catch (error) {
    // Never fail a green run over cleanup.
    console.warn('[e2e teardown] cleanup did not complete:', error);
  } finally {
    await api.dispose();
  }
}
