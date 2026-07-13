import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';

/** A validated way to invoke the MRD Viz backend: `command` plus fixed leading args. */
export interface ResolvedBackend {
	command: string;
	baseArgs: string[];
	source: string;
}

export type BackendResolution =
	| { ok: true; backend: ResolvedBackend }
	| { ok: false; tried: string[] };

let cachedBackend: ResolvedBackend | undefined;

/** Drop the cached backend so the next resolve re-probes (e.g. after a settings change). */
export function invalidateBackendCache(): void {
	cachedBackend = undefined;
}

/**
 * Find the first candidate whose `--version` probe succeeds, in priority order.
 * The result is cached for the session; call {@link invalidateBackendCache} to reset.
 */
export async function resolveBackend(context: vscode.ExtensionContext, validationTimeoutMs: number): Promise<BackendResolution> {
	if (cachedBackend) {
		return { ok: true, backend: cachedBackend };
	}

	const tried: string[] = [];
	for (const candidate of backendCandidates(context)) {
		if (await validateBackend(candidate, validationTimeoutMs)) {
			cachedBackend = candidate;
			return { ok: true, backend: candidate };
		}
		tried.push(candidate.source);
	}

	return { ok: false, tried };
}

export function getConfiguredPythonPath(): string | undefined {
	const inspected = vscode.workspace.getConfiguration('mrdViz').inspect<string>('pythonPath');
	const value = inspected?.workspaceFolderValue ?? inspected?.workspaceValue ?? inspected?.globalValue;
	return value?.trim() || undefined;
}

function* backendCandidates(context: vscode.ExtensionContext): Generator<ResolvedBackend> {
	const pythonBaseArgs = ['-m', 'mrd_viz.cli'];

	// 1. Explicit user override.
	const configured = getConfiguredPythonPath();
	if (configured) {
		yield { command: configured, baseArgs: pythonBaseArgs, source: `mrdViz.pythonPath setting (${configured})` };
	}

	// 2. Backend binary bundled in the VSIX (populated by the standalone-binary build).
	const bundledBinary = bundledBinaryPath(context);
	if (bundledBinary) {
		yield { command: bundledBinary, baseArgs: [], source: `bundled backend (${bundledBinary})` };
	}

	// 3. Managed virtual environment provisioned into global storage.
	const managedVenv = managedVenvPython(context);
	if (managedVenv) {
		yield { command: managedVenv, baseArgs: pythonBaseArgs, source: `managed environment (${managedVenv})` };
	}

	// 4. Repo virtual environment (F5 dev host / contributors).
	const developmentVenv = developmentVenvPython(context);
	if (developmentVenv) {
		yield { command: developmentVenv, baseArgs: pythonBaseArgs, source: `development environment (${developmentVenv})` };
	}

	// 5. A Python interpreter on PATH.
	for (const command of ['python', 'python3']) {
		yield { command, baseArgs: pythonBaseArgs, source: `"${command}" on PATH` };
	}
}

function validateBackend(candidate: ResolvedBackend, timeoutMs: number): Promise<boolean> {
	const timeout = Math.min(Math.max(timeoutMs, 1000), 15000);
	return new Promise(resolve => {
		execFile(
			candidate.command,
			[...candidate.baseArgs, '--version'],
			{ timeout, windowsHide: true },
			error => resolve(!error),
		);
	});
}

function pythonExecutableRelative(): string {
	return process.platform === 'win32' ? path.join('Scripts', 'python.exe') : path.join('bin', 'python');
}

function bundledBinaryPath(context: vscode.ExtensionContext): string | undefined {
	const name = process.platform === 'win32' ? 'mrd-viz.exe' : 'mrd-viz';
	const candidate = path.join(context.extensionUri.fsPath, 'media', 'backend', name);
	return existsSync(candidate) ? candidate : undefined;
}

function managedVenvPython(context: vscode.ExtensionContext): string | undefined {
	const candidate = path.join(context.globalStorageUri.fsPath, 'backend-venv', pythonExecutableRelative());
	return existsSync(candidate) ? candidate : undefined;
}

function developmentVenvPython(context: vscode.ExtensionContext): string | undefined {
	const candidate = path.resolve(context.extensionUri.fsPath, '..', '..', 'backend', '.venv', pythonExecutableRelative());
	return existsSync(candidate) ? candidate : undefined;
}
