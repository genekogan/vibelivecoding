# Livecode E2E contract

The isolated E2E runner may bind only:

- app server: `127.0.0.1:4112`;
- mock server: `127.0.0.1:4113`.

Allowed boot/build commands are the tracked commands in `e2e/config.mjs`:
Python's read-only static HTTP server and exact runtime dependency installation.
The `three-live-catalog-growth` regression may additionally run the tracked
`e2e/helpers/three-runtime-growth-probe.mjs install|remove` helper and
`npm run catalog --prefix threejs/browser`. Its teardown is mandatory even when
an assertion fails; the final registry must return to 200 records and the
authoritative aggregate hash.
Runs use Playwright MCP's isolated ephemeral browser profile. They must not use
the user's normal browser profile, mutate livecode databases, contact real
third-party APIs or touch the existing servers on ports 8766/9866.

Repair loops are capped at three attempts. Stop earlier when the same assertion
fails twice without a relevant diff. Every terminal PASS/PARTIAL/FAIL/ABORT run
must write its summary, run narrative, screenshots and dashboard, then tear down
the isolated server. `.e2e/` is ephemeral and gitignored; `e2e/` scenarios and
fixtures are tracked.

The Three.js browser is a workshop validator. E2E may assert navigation,
controls, persistence, evidence labels, console cleanliness and rendered-canvas
presence. It must not convert a visually present workshop fixture into accepted
artistic or renderer evidence.
