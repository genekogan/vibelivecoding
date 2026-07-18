import { ROUNDED_BOX_LULLABY_POST_OFFICE_ENTRY } from '../rounded-box-lullaby-post-office/scene.mjs';

const ID = 'scene.201.runtime-growth-probe';
const base = ROUNDED_BOX_LULLABY_POST_OFFICE_ENTRY;
const manifest = Object.freeze({
  ...base.manifest,
  id: ID,
  title: 'Runtime Growth Probe',
  thesis: 'A temporary valid preflight proves that an already-open browser appends a newly built scene and refreshes its source-bound catalog status without reload.',
  tags: Object.freeze(['runtime-growth-probe', 'temporary-e2e-preflight', 'append-only-discovery']),
  targets: Object.freeze(base.manifest.targets.map((target) => Object.freeze({ ...target, owner: ID }))),
  evidence: Object.freeze([{ id: `${ID}:temporary-wrapper`, claim: 'already-open-browser-appends-one-newly-built-safe-preflight-without-reload', status: 'accepted', artifact: 'threejs/catalog/preflight/runtime-growth-probe/scene.mjs', artifactHash: base.manifest.contentHash, threeRevision: '185', browser: null, backend: 'node-webgl-compat', deviceProfile: 'temporary-live-growth-rehearsal', viewport: null, dpr: null, notes: 'Temporary wrapper around an existing repository-original factory; deleted after the live discovery receipt is captured.' }]),
  provenance: Object.freeze([{ sourceId: 'original:runtime-growth-probe', reuse: 'original', notes: 'Temporary repository-local wrapper used only to prove hot catalog discovery; no external asset or artist style is used.' }]),
});

export const RUNTIME_GROWTH_PROBE_ENTRY = Object.freeze({
  accent: '#b7ff5a',
  stage: 'preflight-runtime-growth-probe',
  ordinal: 201,
  review: Object.freeze({
    label: 'TEMPORARY HOT-GROWTH PROBE',
    durationCycles: 12,
    defaultSeed: '201201',
    alternateSeeds: Object.freeze(['301201']),
    acceptance: 'temporary-proof-only-never-artistic-catalog-content',
    workOrder: 'e2e/scenarios/regression/07-three-live-catalog-growth.md',
    invariant: 'The already-open browser must add this exact safe record once, update counts and hashes, and remain live without reload.',
    prohibitedCliche: 'This proof wrapper is not an authored Scene 201 and must be removed after the rehearsal.',
  }),
  manifest,
  factory: base.factory,
});
