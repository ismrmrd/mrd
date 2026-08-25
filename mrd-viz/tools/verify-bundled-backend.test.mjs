import assert from 'node:assert/strict';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { test } from 'node:test';

import { verifyBundledBackend } from './verify-bundled-backend.mjs';

async function fixture(t) {
	const directory = await mkdtemp(path.join(tmpdir(), 'mrd-viz-backend-'));
	t.after(() => rm(directory, { recursive: true, force: true }));
	await mkdir(path.join(directory, '_internal'), { recursive: true });
	await writeFile(path.join(directory, 'mrd-viz'), 'binary');
	await writeFile(path.join(directory, '_internal', 'runtime'), 'runtime');
	return directory;
}

test('returns release manifest data for a valid one-dir bundle', async t => {
	const directory = await fixture(t);
	const manifest = await verifyBundledBackend('linux-x64', directory, () => ({
		status: 0,
		stdout: 'mrd-viz 0.1.0\n',
		stderr: '',
	}));

	assert.equal(manifest.schemaVersion, 1);
	assert.equal(manifest.target, 'linux-x64');
	assert.equal(manifest.backendVersion, '0.1.0');
	assert.equal(manifest.executable, 'mrd-viz');
	assert.equal(manifest.executableBytes, 6);
	assert.match(manifest.executableSha256, /^[a-f0-9]{64}$/);
});

test('rejects a one-dir bundle without its runtime', async t => {
	const directory = await fixture(t);
	await rm(path.join(directory, '_internal'), { recursive: true });
	await assert.rejects(
		() => verifyBundledBackend('linux-x64', directory),
		/ENOENT/,
	);
});

test('rejects malformed version output', async t => {
	const directory = await fixture(t);
	await assert.rejects(
		() => verifyBundledBackend('linux-x64', directory, () => ({
			status: 0,
			stdout: 'unexpected\n',
			stderr: '',
		})),
		/Unexpected bundled backend version output/,
	);
});
