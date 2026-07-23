import { execFile, type ExecFileException } from 'node:child_process';
import { existsSync } from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';

/** A validated way to invoke the MRD Viz backend: `command` plus fixed leading args. */
export interface ResolvedBackend {
	command: string;
	baseArgs: string[];
	source: string;
}

/** A candidate that was probed but rejected, plus the reason its `--version` probe failed. */
export interface BackendAttempt {
	source: string;
	/** Human-readable failure reason (captured probe stderr, or the spawn error). */
	detail?: string;
}

export type BackendResolution =
	| { ok: true; backend: ResolvedBackend }
	| { ok: false; tried: BackendAttempt[] };

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

	const tried: BackendAttempt[] = [];
	for (const candidate of backendCandidates(context)) {
		const probe = await validateBackend(candidate, validationTimeoutMs);
		if (probe.ok) {
			cachedBackend = candidate;
			return { ok: true, backend: candidate };
		}
		tried.push({ source: candidate.source, detail: probe.detail });
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

interface ProbeResult {
	ok: boolean;
	/** Failure reason when `ok` is false. */
	detail?: string;
}

function validateBackend(candidate: ResolvedBackend, timeoutMs: number): Promise<ProbeResult> {
	const timeout = Math.min(Math.max(timeoutMs, 1000), 15000);
	return new Promise(resolve => {
		execFile(
			candidate.command,
			[...candidate.baseArgs, '--version'],
			{ timeout, windowsHide: true },
			(error, _stdout, stderr) => {
				if (!error) {
					resolve({ ok: true });
					return;
				}
				resolve({ ok: false, detail: describeProbeFailure(error, stderr) });
			},
		);
	});
}

/**
 * Turn a failed `--version` probe into a concise, user-facing reason. The captured stderr is
 * preferred because it carries the actionable message (e.g. a `GLIBC_2.38 not found` linker
 * error, or a `ModuleNotFoundError: No module named 'mrd_viz'`); the spawn error is a fallback
 * for cases with no output, such as a missing command (ENOENT) or a probe timeout.
 */
function describeProbeFailure(error: ExecFileException, stderr: string): string {
	const trimmedStderr = stderr.trim();
	if (trimmedStderr) {
		return truncateForDisplay(collapseToLastLines(trimmedStderr, 4));
	}
	if (error.code === 'ENOENT') {
		return 'command not found';
	}
	if (error.killed) {
		return 'timed out before responding';
	}
	return truncateForDisplay(error.message.trim() || 'probe failed');
}

function collapseToLastLines(text: string, maxLines: number): string {
	const lines = text.split(/\r?\n/).filter(line => line.trim().length > 0);
	return lines.slice(-maxLines).join('\n');
}

function truncateForDisplay(text: string): string {
	const limit = 600;
	return text.length > limit ? `${text.slice(0, limit)}\u2026` : text;
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
	const candidate = managedVenvPythonPath(context);
	return existsSync(candidate) ? candidate : undefined;
}

/** Directory where the managed backend virtual environment is (or would be) provisioned. */
export function managedVenvDirectory(context: vscode.ExtensionContext): string {
	return path.join(context.globalStorageUri.fsPath, 'backend-venv');
}

/** Path to the interpreter inside the managed backend virtual environment (may not exist yet). */
export function managedVenvPythonPath(context: vscode.ExtensionContext): string {
	return path.join(managedVenvDirectory(context), pythonExecutableRelative());
}

function developmentVenvPython(context: vscode.ExtensionContext): string | undefined {
	const candidate = path.resolve(context.extensionUri.fsPath, '..', '..', 'backend', '.venv', pythonExecutableRelative());
	return existsSync(candidate) ? candidate : undefined;
}
