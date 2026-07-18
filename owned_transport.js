/*
 * Owned Strudel transport for the unified livecode host.
 *
 * @strudel/web's initStrudel() creates a module-scoped scheduler that callers
 * cannot read or control. This adapter intentionally never calls initStrudel().
 * It prebakes the language/audio scope, creates one core repl() with one owned
 * AudioContext-backed Cyclist, and publishes a provenance-rich transport frame.
 */
(function installOwnedTransportFactory(global) {
    "use strict";

    const FORMAT = "livecode-owned-strudel-transport-v1";
    const finite = (value) => Number.isFinite(Number(value)) ? Number(value) : null;
    const clone = (value) => JSON.parse(JSON.stringify(value));
    const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

    const sameDescriptor = (left, right) => {
        if (!left || !right) return left === right;
        return left.value === right.value
            && left.get === right.get
            && left.set === right.set
            && left.writable === right.writable
            && left.enumerable === right.enumerable
            && left.configurable === right.configurable;
    };

    async function waitForGlobals(names, timeoutMs = 15000) {
        const began = performance.now();
        while (performance.now() - began < timeoutMs) {
            const missing = names.filter((name) => typeof global[name] === "undefined");
            if (!missing.length) return;
            await delay(50);
        }
        const missing = names.filter((name) => typeof global[name] === "undefined");
        throw new Error(`Owned Strudel transport missing globals: ${missing.join(", ")}`);
    }

    class OwnedStrudelTransport {
        constructor(options = {}) {
            this.options = options;
            this.repl = null;
            this.scheduler = null;
            this.currentPattern = null;
            this.ready = false;
            this.playing = false;
            this.cps = finite(options.cps) || 0.5;
            this.generation = 1;
            this.serverGeneration = finite(options.serverGeneration) || 0;
            this.reconnectPolicy = options.reconnectPolicy || "declared-hard-reset";
            this.frozenCycle = 0;
            this.schedulerQueryCycle = 0;
            this.activeSeconds = 0;
            this.lastAudioTime = null;
            this.lastReset = null;
            this.lastReason = "construct";
            this.lastEvalError = null;
            this.lastSchedulerError = null;
            this.resetTimer = null;
            this.resetReject = null;
            this.strudelGlobals = new Map();
            this.p5GlobalsRestored = 0;
            this.lastScheduledOutput = null;
            this.scheduledOutputs = [];
        }

        get stateRoot() {
            return global.state || (global.state = {});
        }

        getAudioContext() {
            return typeof global.getAudioContext === "function" ? global.getAudioContext() : null;
        }

        audioSnapshot() {
            const context = this.getAudioContext();
            if (!context) return null;
            let output = null;
            try { output = context.getOutputTimestamp?.() || null; } catch (_) {}
            return {
                state: context.state,
                currentTime: finite(context.currentTime),
                sampleRate: finite(context.sampleRate),
                baseLatency: finite(context.baseLatency),
                outputLatency: finite(context.outputLatency),
                outputContextTime: finite(output?.contextTime),
                outputPerformanceTime: finite(output?.performanceTime),
            };
        }

        async init() {
            await waitForGlobals([
                "defaultPrebake",
                "repl",
                "transpiler",
                "webaudioOutput",
                "getAudioContext",
                "Pattern",
            ]);

            const p5Deadline = performance.now() + 15000;
            while (!global.__livecodeP5Globals && performance.now() < p5Deadline) {
                await delay(25);
            }
            if (!global.__livecodeP5Globals) {
                throw new Error("Owned Strudel transport timed out waiting for p5 global-mode setup");
            }

            if (typeof global.miniAllStrings === "function") global.miniAllStrings();
            const globalsBeforePrebake = new Map(
                Object.getOwnPropertyNames(global).map((name) => [
                    name,
                    Object.getOwnPropertyDescriptor(global, name),
                ]),
            );
            await global.defaultPrebake();

            const candidateNames = new Set([
                ...(global.__strudelExportNames || []),
                ...Object.getOwnPropertyNames(global),
            ]);
            for (const name of candidateNames) {
                const after = Object.getOwnPropertyDescriptor(global, name);
                const before = globalsBeforePrebake.get(name);
                if (after && ((global.__strudelExportNames || []).includes(name) || !sameDescriptor(before, after))) {
                    this.strudelGlobals.set(name, after);
                }
            }

            // Visual code keeps p5 semantics between evaluations. This also
            // prevents accidental Pattern-valued FPS readings and draw errors.
            for (const [name, descriptor] of Object.entries(global.__livecodeP5Globals)) {
                try {
                    Object.defineProperty(global, name, descriptor);
                    this.p5GlobalsRestored += 1;
                } catch (_) {}
            }

            this.repl = global.repl({
                getTime: () => global.getAudioContext().currentTime,
                defaultOutput: (hap, deadline, duration, cps) =>
                    this.scheduleOutput(hap, deadline, duration, cps),
                transpiler: global.transpiler,
                onSchedulerError: (error) => {
                    this.lastSchedulerError = error?.message || String(error);
                    this.options.onError?.("scheduler", error);
                    this.publish("scheduler-error");
                },
                onEvalError: (error) => {
                    this.lastEvalError = error?.message || String(error);
                    this.options.onError?.("evaluate", error);
                },
                onToggle: (started) => {
                    const context = this.getAudioContext();
                    this.playing = !!started;
                    this.lastAudioTime = finite(context?.currentTime);
                    this.publish(started ? "scheduler-start" : "scheduler-stop");
                },
            });
            this.scheduler = this.repl.scheduler;
            this.scheduler.setCps(this.cps);
            this.ready = true;

            // Compatibility surfaces route into the one owned scheduler. The
            // web bundle's hidden scheduler is never constructed.
            const adapter = this;
            global.Pattern.prototype.play = function ownedPatternPlay() {
                adapter.setPattern(this, true);
                return this;
            };
            global.evaluate = (code, autoplay = true) => adapter.evaluate(code, autoplay);
            global.hush = () => adapter.hush("global-hush");
            global.setcps = (value) => adapter.setCps(value, "global-setcps");
            global.setCps = global.setcps;
            global.__livecodeTransport = this;
            this.publish("initialized");
            return this;
        }

        scheduleOutput(hap, deadline, duration, cps) {
            const context = this.getAudioContext();
            const callbackAudioTime = finite(context?.currentTime);
            const deadlineSeconds = finite(deadline);
            const targetAudioTime = callbackAudioTime == null || deadlineSeconds == null
                ? null
                : callbackAudioTime + deadlineSeconds;
            const wholeBegin = finite(hap?.whole?.begin);
            const eventCps = finite(cps) || this.cps;
            const observation = {
                wholeBegin,
                wholeEnd: finite(hap?.whole?.end),
                callbackAudioTime,
                targetAudioTime,
                deadlineSeconds,
                durationSeconds: finite(duration),
                cps: eventCps,
                performanceTime: performance.now(),
            };
            if (wholeBegin != null && targetAudioTime != null) {
                this.lastScheduledOutput = observation;
                this.scheduledOutputs.push(observation);
                if (this.scheduledOutputs.length > 32) this.scheduledOutputs.shift();
            }
            return global.webaudioOutput(hap, deadline, duration, cps);
        }

        async withStrudelGlobals(callback) {
            const previous = new Map();
            for (const [name, descriptor] of this.strudelGlobals) {
                previous.set(name, Object.getOwnPropertyDescriptor(global, name));
                try { Object.defineProperty(global, name, descriptor); }
                catch (_) {}
            }
            try {
                return await callback();
            } finally {
                for (const [name, descriptor] of previous) {
                    try {
                        if (descriptor) Object.defineProperty(global, name, descriptor);
                        else delete global[name];
                    } catch (_) {}
                }
            }
        }

        async ensureAudioRunning() {
            const context = this.getAudioContext();
            if (context?.state === "suspended") await context.resume();
            return context;
        }

        rawSchedulerCycle() {
            if (!this.scheduler || !this.playing) return this.schedulerQueryCycle;
            try {
                const cycle = finite(this.scheduler.now());
                return cycle == null ? this.schedulerQueryCycle : Math.max(0, cycle);
            } catch (_) {
                return this.schedulerQueryCycle;
            }
        }

        updateTime() {
            const context = this.getAudioContext();
            const audioTime = finite(context?.currentTime);
            const running = this.playing && context?.state === "running";
            if (running) {
                if (this.lastAudioTime != null && audioTime != null) {
                    const deltaSeconds = Math.max(0, audioTime - this.lastAudioTime);
                    this.activeSeconds += deltaSeconds;
                    // A scheduler's query cursor contains lookahead and can jump
                    // when setCps() changes the multiplier on that lookahead.
                    // The public cycle is therefore an AudioContext-clocked,
                    // phase-continuous integral of CPS; raw Cyclist truth stays
                    // separately observable below.
                    this.frozenCycle += deltaSeconds * this.cps;
                }
                this.schedulerQueryCycle = this.rawSchedulerCycle();
            }
            this.lastAudioTime = audioTime;
            return { context, audioTime, running };
        }

        snapshot(reason = this.lastReason) {
            const { context, running } = this.updateTime();
            const audio = this.audioSnapshot();
            const cycle = Math.max(0, finite(this.frozenCycle) || 0);
            const outputAge = audio?.currentTime != null && audio?.outputContextTime != null
                ? Math.max(0, audio.currentTime - audio.outputContextTime)
                : null;
            const outputAnchor = this.lastScheduledOutput;
            const audioGraphCycle = outputAnchor?.wholeBegin != null
                && outputAnchor?.targetAudioTime != null
                && audio?.currentTime != null
                ? outputAnchor.wholeBegin
                    + (audio.currentTime - outputAnchor.targetAudioTime) * outputAnchor.cps
                : cycle;
            const presentationCycle = outputAnchor?.wholeBegin != null
                && outputAnchor?.targetAudioTime != null
                && audio?.outputContextTime != null
                ? outputAnchor.wholeBegin
                    + (audio.outputContextTime - outputAnchor.targetAudioTime) * outputAnchor.cps
                : outputAge == null ? null : cycle - outputAge * this.cps;
            let confidence = "uninitialized";
            if (this.ready && !this.playing) confidence = "frozen-stopped";
            else if (this.ready && running) confidence = "audio-context-scheduler";
            else if (this.ready && this.playing && context?.state !== "running") confidence = "held-audio-suspended";
            return {
                format: FORMAT,
                initialized: this.ready,
                source: "owned-webaudio-Cyclist",
                confidence,
                generation: this.generation,
                serverGeneration: this.serverGeneration,
                reconnectPolicy: this.reconnectPolicy,
                playing: this.playing,
                cps: this.cps,
                cycle,
                beat: cycle * 4,
                bar: cycle,
                phase: ((cycle * 4) % 1 + 1) % 1,
                cyclePhase: ((cycle % 1) + 1) % 1,
                schedulerQueryCycle: finite(this.schedulerQueryCycle),
                schedulerQueryDeltaCycles: finite(this.schedulerQueryCycle) - cycle,
                audioGraphCycleEstimate: finite(audioGraphCycle),
                seconds: this.activeSeconds,
                presentationCycleEstimate: presentationCycle,
                presentationOffsetSeconds: outputAge == null ? null : -outputAge,
                errorBoundSeconds: null,
                audio,
                visibility: document.visibilityState,
                lastScheduledOutput: outputAnchor,
                scopedGlobals: this.strudelGlobals.size,
                p5GlobalsRestored: this.p5GlobalsRestored,
                lastReason: reason,
                lastReset: this.lastReset,
                lastEvalError: this.lastEvalError,
                lastSchedulerError: this.lastSchedulerError,
            };
        }

        publish(reason = "frame") {
            this.lastReason = reason;
            const value = this.snapshot(reason);
            this.stateRoot.transport = value;
            return value;
        }

        frame() {
            return this.publish("frame");
        }

        setPattern(pattern, autostart = true) {
            if (!this.ready || !this.scheduler) throw new Error("Owned transport is not initialized");
            this.currentPattern = pattern;
            this.scheduler.setPattern(pattern, autostart);
            return this.publish("set-pattern");
        }

        async evaluate(code, autoplay = true) {
            if (!this.ready || !this.repl) throw new Error("Owned transport is not initialized");
            await this.ensureAudioRunning();
            this.lastEvalError = null;
            // The third repl() flag is "reset before evaluate". Keep it false:
            // scheduler.stop() would destroy phase continuity every time a named
            // track changes. setPattern(pattern, true) starts only when stopped
            // and otherwise swaps the pattern on the running transport.
            const pattern = await this.withStrudelGlobals(
                () => this.repl.evaluate(code, autoplay, false),
            );
            if (this.repl.state.evalError || !pattern) {
                const error = this.repl.state.evalError || new Error("Strudel evaluation returned no pattern");
                throw error;
            }
            this.currentPattern = pattern;
            this.publish(autoplay ? "evaluate-play" : "evaluate-only");
            return pattern;
        }

        setCps(value, reason = "set-cps") {
            const cps = finite(value);
            if (!(cps > 0)) throw new Error(`Invalid CPS: ${value}`);
            this.updateTime();
            this.cps = cps;
            this.scheduler?.setCps(cps);
            return this.publish(reason);
        }

        cancelReset(reason = "cancelled") {
            if (this.resetTimer != null) {
                clearTimeout(this.resetTimer);
                this.resetTimer = null;
                this.resetReject?.(new Error(`Quantized reset ${reason}`));
                this.resetReject = null;
            }
        }

        hardReset(reason = "hard-reset", detail = null, restart = this.playing) {
            this.cancelReset("superseded");
            this.updateTime();
            const beforeCycle = this.frozenCycle;
            const beforeGeneration = this.generation;
            this.scheduler?.stop();
            this.frozenCycle = 0;
            this.schedulerQueryCycle = 0;
            this.activeSeconds = 0;
            this.lastScheduledOutput = null;
            this.scheduledOutputs = [];
            this.lastAudioTime = finite(this.getAudioContext()?.currentTime);
            this.generation += 1;
            if (restart && this.currentPattern) this.scheduler.setPattern(this.currentPattern, true);
            this.lastReset = {
                reason,
                beforeCycle,
                beforeGeneration,
                generation: this.generation,
                detail,
                performanceTime: performance.now(),
                audioTime: finite(this.getAudioContext()?.currentTime),
            };
            return this.publish(reason);
        }

        hush(reason = "hush") {
            this.currentPattern = null;
            const value = this.hardReset(reason, { policy: "hard-reset" }, false);
            if (typeof global.silence !== "undefined") this.scheduler?.setPattern(global.silence, false);
            return this.publish(reason);
        }

        async resetAtBoundary(quantumCycles = 1, reason = "quantized-reset") {
            const quantum = finite(quantumCycles);
            if (!(quantum > 0)) throw new Error(`Invalid reset quantum: ${quantumCycles}`);
            if (!this.playing) return this.hardReset(reason, { quantumCycles: quantum, immediate: true }, false);
            const context = await this.ensureAudioRunning();
            if (!context || context.state !== "running") throw new Error("Cannot schedule quantized reset without a running AudioContext");
            this.cancelReset("replaced");
            this.updateTime();
            const requestedFromCycle = this.frozenCycle;
            const targetCycle = (Math.floor(requestedFromCycle / quantum) + 1) * quantum;
            const targetAudioTime = context.currentTime + (targetCycle - requestedFromCycle) / this.cps;
            const delayMs = Math.max(0, (targetAudioTime - context.currentTime) * 1000);
            return new Promise((resolve, reject) => {
                this.resetReject = reject;
                const commitWhenAudioReachesBoundary = () => {
                    // setTimeout follows the wall clock while AudioContext time
                    // freezes during suspension. Re-check the authoritative
                    // audio clock so a hidden/suspended tab cannot reset early.
                    const remainingSeconds = targetAudioTime - context.currentTime;
                    if (remainingSeconds > 0.002) {
                        this.resetTimer = setTimeout(
                            commitWhenAudioReachesBoundary,
                            Math.max(2, remainingSeconds * 1000),
                        );
                        return;
                    }
                    this.resetTimer = null;
                    this.resetReject = null;
                    this.updateTime();
                    const observedCycle = this.frozenCycle;
                    const cycleError = observedCycle - targetCycle;
                    const errorSeconds = cycleError / this.cps;
                    const value = this.hardReset(reason, {
                        quantumCycles: quantum,
                        requestedFromCycle,
                        targetCycle,
                        targetAudioTime,
                        observedCycle,
                        cycleError,
                        errorSeconds,
                    }, true);
                    resolve(value);
                };
                this.resetTimer = setTimeout(commitWhenAudioReachesBoundary, delayMs);
            });
        }

        configure(options = {}) {
            const nextServerGeneration = finite(options.serverGeneration);
            const generationChanged = nextServerGeneration != null
                && nextServerGeneration !== this.serverGeneration;
            if (nextServerGeneration != null) this.serverGeneration = nextServerGeneration;
            if (options.reconnectPolicy) this.reconnectPolicy = String(options.reconnectPolicy);
            if (generationChanged && this.reconnectPolicy === "declared-hard-reset") {
                // A websocket/browser reconnection is deliberately a new epoch.
                // The server restores the current pattern immediately afterward.
                this.hush(options.reason || "browser-connect-hard-reset");
            }
            if (finite(options.cps) > 0) this.setCps(options.cps, options.reason || "configure-cps");
            return this.publish(options.reason || "configure");
        }

        serializableSnapshot(reason = "snapshot") {
            return clone(this.publish(reason));
        }
    }

    global.createOwnedStrudelTransport = async function createOwnedStrudelTransport(options = {}) {
        const transport = new OwnedStrudelTransport(options);
        return transport.init();
    };
})(window);
