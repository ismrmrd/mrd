import { execFile, type ExecFileException } from 'node:child_process';
import { existsSync } from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';

/** How a backend candidate was selected. Drives tailored failure messaging in the webview. */
export type BackendKind = 'override' | 'bundled' | 'development';

/** A validated way to invoke the MRD Viz backend: `command` plus fixed leading args. */
export interface ResolvedBackend {
	command: string;
	baseArgs: string[];
	source: string;
	kind: BackendKind;
	/** For an override candidate, which setting supplied the path (`mrdViz.backendPath` or legacy `mrdViz.pythonPath`). */
	settingKey?: string;
}

/** A candidate that was probed but rejected, plus the reason its `--version` probe failed. */
export interface BackendAttempt {
	source: string;
	/** Which tier this candidate belonged to, so the UI can distinguish a broken override from a missing binary. */
	kind?: BackendKind;
	/** For an override attempt, the setting that supplied the path, so the UI points at the right one. */
	settingKey?: string;
	/** Concise, webview-friendly failure reason (last lines of probe stderr, or the spawn error). */
	detail?: string;
	/** Complete captured probe output, logged in full to the output channel (never truncated). */
	detailFull?: string;
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

	const configured = getConfiguredBackendPath();
	const candidates = planBackendCandidates({
		configuredPath: configured?.path,
		configuredSettingKey: configured?.settingKey,
		bundledBinaryPath: bundledBinaryPath(context),
		developmentVenvPath: developmentVenvPython(context),
		isDevelopment: context.extensionMode === vscode.ExtensionMode.Development,
	});

	const tried: BackendAttempt[] = [];
	for (const candidate of candidates) {
		const probe = await validateBackend(candidate, validationTimeoutMs);
		if (probe.ok) {
			cachedBackend = candidate;
			return { ok: true, backend: candidate };
		}
		tried.push({ source: candidate.source, kind: candidate.kind, settingKey: candidate.settingKey, detail: probe.detail, detailFull: probe.detailFull });
	}

	return { ok: false, tried };
}

const PYTHON_MODULE_ARGS = ['-m', 'mrd_viz.cli'];
const BACKEND_PATH_SETTING = 'mrdViz.backendPath';
const LEGACY_PATH_SETTING = 'mrdViz.pythonPath';

/**
 * The developer override, if set: the machine-scoped `mrdViz.backendPath`, or an explicitly set
 * (non-default) legacy `mrdViz.pythonPath` for backward compatibility. Returns the path plus which
 * setting supplied it (so messaging points at the right one), or undefined when the user has
 * configured nothing — the signal that this is an end-user install that should use the bundled
 * backend.
 */
export function getConfiguredBackendPath(): { path: string; settingKey: string } | undefined {
	const config = vscode.workspace.getConfiguration('mrdViz');
	const backendPath = config.get<string>('backendPath')?.trim();
	if (backendPath) {
		return { path: backendPath, settingKey: BACKEND_PATH_SETTING };
	}
	// Back-compat: honor an explicitly set legacy mrdViz.pythonPath (ignoring any default value).
	const legacy = config.inspect<string>('pythonPath');
	const legacyValue = (legacy?.workspaceFolderValue ?? legacy?.workspaceValue ?? legacy?.globalValue)?.trim();
	return legacyValue ? { path: legacyValue, settingKey: LEGACY_PATH_SETTING } : undefined;
}

/** Inputs to {@link planBackendCandidates}; plain data so the ordering logic stays pure and testable. */
export interface BackendCandidateInputs {
	/** Developer override path (interpreter or binary), or undefined when unset. */
	configuredPath?: string;
	/** Which setting supplied `configuredPath` (`mrdViz.backendPath` or legacy `mrdViz.pythonPath`). */
	configuredSettingKey?: string;
	/** Path to the bundled binary if present in the VSIX, else undefined. */
	bundledBinaryPath?: string;
	/** Path to the repo `backend/.venv` interpreter if present, else undefined. */
	developmentVenvPath?: string;
	/** True when the extension host is the F5 Development host (`ExtensionMode.Development`). */
	isDevelopment: boolean;
}

/**
 * Deterministic, two-tier candidate order (see docs/BACKEND_INSTALL_MODES.md):
 *
 * - If a developer override is set, it is the ONLY candidate — no silent fallback to the bundled
 *   binary, so a broken override fails loudly instead of masking a misconfiguration.
 * - Otherwise (end user / unconfigured) use the bundled binary. In the Development host only, the
 *   repo `backend/.venv` is tried first so contributors run their live checkout.
 */
export function planBackendCandidates(inputs: BackendCandidateInputs): ResolvedBackend[] {
	if (inputs.configuredPath) {
		return [configuredBackend(inputs.configuredPath, inputs.configuredSettingKey)];
	}

	const candidates: ResolvedBackend[] = [];
	if (inputs.isDevelopment && inputs.developmentVenvPath) {
		candidates.push({
			command: inputs.developmentVenvPath,
			baseArgs: PYTHON_MODULE_ARGS,
			source: `development environment (${inputs.developmentVenvPath})`,
			kind: 'development',
		});
	}
	if (inputs.bundledBinaryPath) {
		candidates.push({
			command: inputs.bundledBinaryPath,
			baseArgs: [],
			source: `bundled backend (${inputs.bundledBinaryPath})`,
			kind: 'bundled',
		});
	}
	return candidates;
}

/** Build the override candidate, treating an `mrd-viz` executable as a binary and anything else as an interpreter. */
function configuredBackend(configuredPath: string, settingKey: string = BACKEND_PATH_SETTING): ResolvedBackend {
	const baseArgs = looksLikeBackendBinary(configuredPath) ? [] : PYTHON_MODULE_ARGS;
	return { command: configuredPath, baseArgs, source: `${settingKey} setting (${configuredPath})`, kind: 'override', settingKey };
}

/** Whether a configured path points at the standalone backend binary rather than a Python interpreter. */
function looksLikeBackendBinary(configuredPath: string): boolean {
	const base = path.basename(configuredPath).toLowerCase();
	return base === 'mrd-viz' || base === 'mrd-viz.exe';
}

interface ProbeResult {
	ok: boolean;
	/** Concise failure reason for the webview when `ok` is false. */
	detail?: string;
	/** Complete captured output for the output channel when `ok` is false. */
	detailFull?: string;
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
				resolve({ ok: false, detail: describeProbeFailure(error, stderr), detailFull: fullProbeFailure(error, stderr) });
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

/**
 * Like {@link describeProbeFailure} but without collapsing or truncation, so the complete probe
 * output can be written to the output channel where a linker/module error may span many lines.
 */
function fullProbeFailure(error: ExecFileException, stderr: string): string {
	const trimmedStderr = stderr.trim();
	if (trimmedStderr) {
		return trimmedStderr;
	}
	if (error.code === 'ENOENT') {
		return 'command not found';
	}
	if (error.killed) {
		return 'timed out before responding';
	}
	return error.message.trim() || 'probe failed';
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
