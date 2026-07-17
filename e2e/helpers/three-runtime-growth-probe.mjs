#!/usr/bin/env node
import { copyFile, mkdir, rm, rmdir, stat } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const fixture = resolve(root, 'e2e/fixtures/three-runtime-growth-probe.scene.mjs');
const targetDir = resolve(root, 'threejs/catalog/preflight/runtime-growth-probe');
const target = resolve(targetDir, 'scene.mjs');
const command = process.argv[2];

async function exists(path) {
  try { await stat(path); return true; }
  catch (error) { if (error.code === 'ENOENT') return false; throw error; }
}

if (command === 'install') {
  if (await exists(target)) throw new Error(`runtime growth probe already installed: ${target}`);
  await mkdir(targetDir, { recursive: false });
  await copyFile(fixture, target);
  process.stdout.write(`${JSON.stringify({ status: 'installed', target })}\n`);
} else if (command === 'remove') {
  await rm(target, { force: true });
  try { await rmdir(targetDir); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  process.stdout.write(`${JSON.stringify({ status: 'removed', target })}\n`);
} else {
  throw new Error('usage: node e2e/helpers/three-runtime-growth-probe.mjs <install|remove>');
}
