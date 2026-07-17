---
id: three-transactional-navigation
tier: smoke
fixture: empty
mocks: []
critical_path: true
---

# Scene navigation uses the transactional dual-slot host

## Preconditions
- Workshop initialized on Clockwork Bloom.

## Steps

1. Navigate to `/threejs/browser/index.html?forceWebGL=1` and wait for "Clockwork Bloom".
   - expect-url: matches `^/threejs/browser/index\.html`
2. Activate the Next scene button and wait for "Orbit Familiar".
   - expect: heading "Orbit Familiar", status containing "unaccepted workshop fixture", transition state returned to active, and no error ledger entries
   - screenshot: orbit-familiar.png
3. Activate Next again and wait for "Signal Chapel".
   - expect: heading "Signal Chapel" and three architecture-specific parameter sliders
   - screenshot: signal-chapel.png
4. Activate Next again and wait for "Mycelial Oracle".
   - expect: heading "Mycelial Oracle", a rendered branching stage, and transition state returned to active
   - screenshot: mycelial-oracle.png
5. Post-run.
   - expect-console: no errors since step 1

## Proof required
- `orbit-familiar.png`
- `signal-chapel.png`
- `mycelial-oracle.png`
