"""Demo p5.js visual composition — builds up layers over time."""

from p5_server import P5Controller
import time

ctrl = P5Controller()
ctrl.start()
print("Open http://localhost:8776/p5.html and click 'Start & Connect'")
ctrl.wait_for_browser(timeout=120)

print("\n--- Starting demo composition ---\n")

# 1. Animated HSB background cycling
print("Layer 1: HSB background cycle")
ctrl.set_layer("bg", """
    colorMode(HSB, 360, 100, 100);
    background((frameCount * 0.5) % 360, 30, 15);
""")
time.sleep(3)

# 2. Central pulsing circle
print("Layer 2: Pulsing circle")
ctrl.set_layer("pulse", """
    let size = 200 + sin(frameCount * 0.05) * 80;
    noStroke();
    fill((frameCount * 2) % 360, 80, 90, 60);
    circle(width / 2, height / 2, size);
""")
time.sleep(3)

# 3. Initialize state for particles
print("Layer 3: Particle system")
ctrl.init_state(particles=[])
ctrl.set_layer("particles", """
    // Add new particle each frame
    if (state.particles.length < 200) {
        state.particles.push({
            x: width / 2 + random(-50, 50),
            y: height / 2 + random(-50, 50),
            vx: random(-2, 2),
            vy: random(-3, -0.5),
            life: 255,
            hue: random(360)
        });
    }
    // Update and draw
    noStroke();
    for (let i = state.particles.length - 1; i >= 0; i--) {
        let p = state.particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.02;
        p.life -= 1.5;
        if (p.life <= 0) { state.particles.splice(i, 1); continue; }
        fill(p.hue, 80, 90, p.life / 255 * 80);
        circle(p.x, p.y, map(p.life, 0, 255, 2, 10));
    }
""")
time.sleep(4)

# 4. Hot-swap: change the background to something different
print("Layer 4: Hot-swap background (darker)")
ctrl.set_layer("bg", """
    colorMode(HSB, 360, 100, 100);
    background((frameCount * 0.3) % 360, 20, 8);
""")
time.sleep(3)

# 5. Add rotating rings
print("Layer 5: Rotating rings")
ctrl.set_layer("rings", """
    noFill();
    strokeWeight(2);
    translate(width / 2, height / 2);
    for (let i = 0; i < 5; i++) {
        let angle = frameCount * 0.02 * (i + 1);
        let radius = 100 + i * 60;
        stroke((frameCount + i * 60) % 360, 70, 90, 50);
        rotate(angle);
        ellipse(0, 0, radius, radius * 0.6);
    }
""")
time.sleep(4)

# 6. Remove layers one by one
print("\n--- Removing layers ---")
for name in ["rings", "particles", "pulse"]:
    print(f"  Removing: {name}")
    ctrl.remove_layer(name)
    time.sleep(1.5)

print("  Clearing all")
ctrl.clear()
time.sleep(1)

print("\n--- Demo complete! ---")
print("The canvas is now clear. Server still running — send more layers!")
print("Try: python p5_send.py --layer test 'background(0); fill(255); circle(width/2, height/2, 300);'")

# Keep server alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ctrl.close()
