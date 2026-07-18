/**
 * Fixture: empty data dir.
 *
 * Preconditions: the ephemeral $EDEN3_DATA_DIR is fresh (no DB yet). Mastra
 * creates tables on first boot. For the `empty` fixture we don't need to
 * seed anything — we just confirm the app is reachable.
 *
 * Fixtures receive { appUrl } and should throw on failure.
 */

export default async function seedEmpty({ appUrl }) {
  const r = await fetch(`${appUrl}/api/agents`);
  if (!r.ok) throw new Error(`empty fixture: /api/agents returned ${r.status}`);
  return { seeded: 'empty' };
}
