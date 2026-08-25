import { createHash } from 'node:crypto';
import { readdir, readFile, stat, writeFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const TARGETS = new Map([
	['linux-x64', 'mrd-viz'],
	['win32-x64', 'mrd-viz.exe'],
	['darwin-arm64', 'mrd-viz'],
	['darwin-x64', 'mrd-viz'],
]);

export async function verifyBundledBackend(target, backendDirectory, run = spawnSync) {
	const executableName = TARGETS.get(target);
	if (!executableName) {
		throw new Error(`Unsupported VS Code target "${target}". Expected one of: ${[...TARGETS.keys()].join(', ')}`);
	}

	const executablePath = path.join(backendDirectory, executableName);
	const executableStat = await stat(executablePath);
	if (!executableStat.isFile() || executableStat.size === 0) {
		throw new Error(`Bundled backend executable is empty or not a file: ${executablePath}`);
	}

	const internalDirectory = path.join(backendDirectory, '_internal');
	const internalEntries = await readdir(internalDirectory);
	if (internalEntries.length === 0) {
		throw new Error(`PyInstaller one-dir runtime is empty: ${internalDirectory}`);
	}

	const result = run(executablePath, ['--version'], { encoding: 'utf8' });
	if (result.error) {
		throw new Error(`Bundled backend version probe failed: ${result.error.message}`);
	}
	if (result.status !== 0) {
		throw new Error(`Bundled backend version probe exited ${result.status}: ${(result.stderr || '').trim()}`);
	}

	const versionOutput = (result.stdout || '').trim();
	const versionMatch = /^mrd-viz\s+(\S+)$/.exec(versionOutput);
	if (!versionMatch) {
		throw new Error(`Unexpected bundled backend version output: ${JSON.stringify(versionOutput)}`);
	}

	const executableBytes = await readFile(executablePath);
	return {
		schemaVersion: 1,
		target,
		backendVersion: versionMatch[1],
		executable: executableName,
		executableBytes: executableStat.size,
		executableSha256: createHash('sha256').update(executableBytes).digest('hex'),
	};
}

async function main() {
	const [target, backendDirectory = 'extension/mrd-viz/media/backend'] = process.argv.slice(2);
	if (!target) {
		throw new Error('Usage: node tools/verify-bundled-backend.mjs <target> [backend-directory]');
	}

	const manifest = await verifyBundledBackend(target, backendDirectory);
	const manifestPath = path.join(backendDirectory, 'backend-manifest.json');
	await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
	console.log(`Verified ${target} bundled backend ${manifest.backendVersion}; wrote ${manifestPath}`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
	main().catch(error => {
		console.error(error instanceof Error ? error.message : String(error));
		process.exitCode = 1;
	});
}
