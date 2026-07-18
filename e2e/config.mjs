/**
 * e2e runner config. EDIT THIS for your project before running any scenarios.
 *
 * This file is tracked in git alongside your scenarios/ and fixtures/. The
 * runner code that reads it lives in the (gitignored) .e2e/ folder.
 */

export const config = {
  // Ports the runner will bind. Pick values that don't collide with your dev server.
  ports: { app: 4112, mock: 4113 },

  boot: {
    // Command + args that start your app in production/built mode.
    // e.g. ['node', 'dist/server.js']  or  ['npm', 'run', 'start']
    command: 'python3',
    args: ['-m', 'http.server', '4112', '--bind', '127.0.0.1', '--directory', '.'],

    // Env vars the app reads. PORT is almost always required.
    env: { PORT: '4112', PYTHONUNBUFFERED: '1' },

    // URL polled during readiness check. Must return 2xx when app is ready.
    readyProbe: 'http://localhost:4112/threejs/browser/index.html?forceWebGL=1',
    readyTimeoutMs: 30_000,

    // Files that must exist before booting. Missing -> "run buildCommand first".
    buildArtifacts: ['threejs/browser/index.html', 'threejs/runtime/node_modules/three/package.json'],
    buildCommand: 'npm install --prefix threejs/runtime --ignore-scripts',
  },

  liveEnvVar: 'E2E_LIVE',

  // Path layout. `e2e/` is authored/tracked (scenarios + fixtures + this config).
  // `.e2e/` is scaffolded tool working state (runner + mocks + ephemeral runs).
  paths: {
    authored: 'e2e',
    scenarios: 'e2e/scenarios',
    fixtures: 'e2e/fixtures',
    tool: '.e2e',
    runs: '.e2e/runs',
    mocks: '.e2e/mocks',
  },
};
