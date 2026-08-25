import { existsSync } from 'node:fs';
import { mkdir, rename, rm } from 'node:fs/promises';
import * as path from 'node:path';
import * as vscode from 'vscode';

import {
	PROVISIONING_LOG_MAX_BUFFER_BYTES,
	PROVISIONING_PYTHON_CANDIDATES,
	PROVISIONING_STEP_TIMEOUT_MS,
	PYPI_PACKAGE_NAME,
	PYTHON_VERSION_PROBE_TIMEOUT_MS,
} from './backendConstants';
import { invalidateBackendCache, managedVenvDirectory, managedVenvPythonPath } from './backendResolver';
import { MrdEditorProvider, MRD_VIEW_TYPE } from './mrdEditorProvider';
import { runProcess } from './subprocess';
import { showWorkflowScaffoldPanel } from './workflowPanel';

const STABLE_RELEASE_URL = 'https://github.com/ismrmrd/mrd/releases/latest';

export function activate(context: vscode.ExtensionContext) {
	const outputChannel = vscode.window.createOutputChannel('MRD Viz');
	context.subscriptions.push(outputChannel);

	const editorProvider = new MrdEditorProvider(context, outputChannel);
	context.subscriptions.push(vscode.window.registerCustomEditorProvider(MRD_VIEW_TYPE, editorProvider, {
		webviewOptions: {
			retainContextWhenHidden: true,
		},
	}));

	context.subscriptions.push(
		vscode.commands.registerCommand('mrd-viz.setUpBackend', () => setUpBackend(context, outputChannel)),
		vscode.commands.registerCommand('mrd-viz.selectInterpreter', () => selectInterpreter()),
		vscode.commands.registerCommand('mrd-viz.openStableInstallLink', () => openStableInstallLink()),
		vscode.commands.registerCommand('mrd-viz.openWorkflowView', () => showWorkflowScaffoldPanel()),
		vscode.workspace.onDidChangeConfiguration(event => {
			if (event.affectsConfiguration('mrdViz.backendPath')) {
				invalidateBackendCache();
			}
		}),
	);

	const disposable = vscode.commands.registerCommand('mrd-viz.openFile', async (resource?: vscode.Uri, selectedResources?: vscode.Uri[]) => {
		const targetUri = await resolveTargetUri(resource, selectedResources);
		if (!targetUri) {
			return;
		}

		try {
			await vscode.commands.executeCommand(...getOpenWithMrdEditorArgs(targetUri));
		} catch (error) {
			const message = error instanceof Error ? error.message : String(error);
			outputChannel.show(true);
			outputChannel.appendLine(`MRD Viz failed to open ${targetUri.fsPath}: ${message}`);
			vscode.window.showErrorMessage(`MRD Viz failed to open ${path.basename(targetUri.fsPath)}: ${message}`);
		}
	});

	context.subscriptions.push(disposable);
}

export function deactivate() {}

export function getOpenWithMrdEditorArgs(targetUri: vscode.Uri): [string, vscode.Uri, string, vscode.TextDocumentShowOptions] {
	return ['vscode.openWith', targetUri, MRD_VIEW_TYPE, {
		preview: false,
		viewColumn: vscode.ViewColumn.Active,
	}];
}

async function resolveTargetUri(resource?: vscode.Uri, selectedResources?: vscode.Uri[]): Promise<vscode.Uri | undefined> {
	const candidate = await pickTargetUri(resource, selectedResources);
	if (!candidate) {
		return undefined;
	}

	if (candidate.scheme !== 'file' || !isMrdFile(candidate.fsPath)) {
		void vscode.window.showWarningMessage(`MRD Viz can only open .mrd files: "${path.basename(candidate.fsPath)}" is not an MRD file.`);
		return undefined;
	}

	return candidate;
}

async function pickTargetUri(resource?: vscode.Uri, selectedResources?: vscode.Uri[]): Promise<vscode.Uri | undefined> {
	if (resource?.scheme === 'file') {
		return resource;
	}

	const firstSelectedResource = selectedResources?.find(item => item.scheme === 'file');
	if (firstSelectedResource) {
		return firstSelectedResource;
	}

	const activeUri = vscode.window.activeTextEditor?.document.uri;
	if (activeUri?.scheme === 'file') {
		return activeUri;
	}

	const selectedFiles = await vscode.window.showOpenDialog({
		canSelectFiles: true,
		canSelectFolders: false,
		canSelectMany: false,
		filters: {
			'MRD files': ['mrd'],
		},
		openLabel: 'Inspect MRD File',
	});

	return selectedFiles?.[0];
}

async function setUpBackend(context: vscode.ExtensionContext, outputChannel: vscode.OutputChannel): Promise<void> {
	const quickPick = await vscode.window.showQuickPick(
		[
			{
				label: 'Use stable release installer (recommended)',
				description: 'No Python/PyPI setup steps. Open the latest GitHub release install link.',
				action: 'stable' as const,
			},
			{
				label: 'Set up backend automatically here',
				description: 'Creates a managed Python environment and installs mrd-viz.',
				action: 'managed' as const,
			},
			{
				label: 'Select backend interpreter manually',
				description: 'Point mrdViz.backendPath at an existing backend environment.',
				action: 'manual' as const,
			},
		],
		{
			placeHolder: 'Choose backend setup mode',
			ignoreFocusOut: true,
		},
	);
	if (!quickPick) {
		return;
	}

	if (quickPick.action === 'stable') {
		await openStableInstallLink();
		return;
	}
	if (quickPick.action === 'manual') {
		await selectInterpreter();
		return;
	}

	await setUpManagedBackend(context, outputChannel);
}

async function setUpManagedBackend(context: vscode.ExtensionContext, outputChannel: vscode.OutputChannel): Promise<void> {
	// If a managed backend is already provisioned, this rebuilds it from scratch, so confirm the
	// reinstall rather than silently clobbering a working environment.
	const alreadyInstalled = existsSync(managedVenvPythonPath(context));
	const confirmLabel = alreadyInstalled ? 'Reinstall' : 'Install';
	const proceed = await vscode.window.showInformationMessage(
		alreadyInstalled
			? 'An MRD Viz backend is already installed in the extension\u2019s storage. Reinstall it? This deletes and rebuilds the private Python virtual environment and re-installs the "mrd_viz" package with pip. It needs a Python 3.12+ interpreter on PATH and network access.'
			: 'Set up the MRD Viz backend automatically? This creates a private Python virtual environment in the extension\u2019s storage and installs the "mrd_viz" package with pip. It needs a Python 3.12+ interpreter on PATH and network access.',
		{ modal: true },
		confirmLabel,
	);
	if (proceed !== confirmLabel) {
		return;
	}

	const installed = await provisionManagedBackend(context, outputChannel);
	if (installed) {
		// Persist the managed venv as the configured backend (machine-scoped) so it becomes a
		// first-class override the resolver reads directly, rather than an implicit candidate.
		await vscode.workspace.getConfiguration('mrdViz').update(
			'backendPath', managedVenvPythonPath(context), vscode.ConfigurationTarget.Global,
		);
		invalidateBackendCache();
		void vscode.window.showInformationMessage(alreadyInstalled ? 'MRD Viz backend reinstalled.' : 'MRD Viz backend installed.');
	}
}

async function openStableInstallLink(): Promise<void> {
	await vscode.env.openExternal(vscode.Uri.parse(STABLE_RELEASE_URL));
}

async function selectInterpreter(): Promise<void> {
	const picked = await vscode.window.showOpenDialog({
		canSelectMany: false,
		canSelectFolders: false,
		openLabel: 'Select interpreter',
		title: 'Select the Python interpreter that has the mrd_viz backend',
	});
	if (!picked || picked.length === 0) {
		return;
	}

	// backendPath is machine-scoped, so this writes to the context-appropriate machine settings
	// (host user settings, or the dev container's remote settings) and cannot leak across that
	// boundary or be committed to a workspace — no narrower-scope clearing needed.
	const config = vscode.workspace.getConfiguration('mrdViz');
	await config.update('backendPath', picked[0].fsPath, vscode.ConfigurationTarget.Global);
	invalidateBackendCache();
	void vscode.window.showInformationMessage('MRD Viz backend updated.');
}

/** A provisioning step that failed, tagged with the human-readable phase for clear reporting. */
class BackendSetupError extends Error {
	constructor(readonly step: string, detail: string) {
		super(detail);
		this.name = 'BackendSetupError';
	}
}

/** Flags applied to every pip call: silence the version-check notice and never block on a prompt. */
const PIP_FLAGS = ['--disable-pip-version-check', '--no-input'];

/**
 * Provision the managed backend virtual environment in global storage: create a venv from a
 * discovered Python 3.12+ interpreter and `pip install` the backend. The caller persists the venv
 * interpreter to `mrdViz.backendPath` on success. Returns true only if every step succeeds; on any
 * failure the half-provisioned venv is removed (so a stale interpreter can't satisfy the resolver
 * probe and then fail at `import mrd_viz`) and the cause is surfaced to the user and the output
 * channel.
 */
async function provisionManagedBackend(context: vscode.ExtensionContext, outputChannel: vscode.OutputChannel): Promise<boolean> {
	const basePython = await findProvisioningPython();
	if (!basePython) {
		void vscode.window.showErrorMessage(
			'MRD Viz could not find a Python 3.12+ interpreter on PATH to build the backend environment. Install Python 3.12 or newer, or use "Select Python Interpreter\u2026" to point at an existing environment.',
		);
		return false;
	}

	const venvDir = managedVenvDirectory(context);
	const venvPython = managedVenvPythonPath(context);
	const installTarget = repoBackendInstallTarget(context) ?? PYPI_PACKAGE_NAME;

	return vscode.window.withProgress(
		{ location: vscode.ProgressLocation.Notification, title: 'Setting up MRD Viz backend', cancellable: false },
		async progress => {
			try {
				await mkdir(path.dirname(venvDir), { recursive: true });

				progress.report({ message: 'Creating virtual environment\u2026' });
				await runProvisioningStep('creating the virtual environment', basePython, ['-m', 'venv', venvDir], outputChannel);

				progress.report({ message: 'Upgrading pip\u2026' });
				await runProvisioningStep('upgrading pip', venvPython, ['-m', 'pip', 'install', ...PIP_FLAGS, '--upgrade', 'pip'], outputChannel);

				progress.report({ message: 'Installing the mrd_viz backend\u2026' });
				// TODO(publish-pypi): the PYPI_PACKAGE_NAME branch only resolves once the backend is
				// published to PyPI; until then setup succeeds only from a repo checkout (editable
				// install) and otherwise fails loudly with the package-not-found hint.
				const installArgs = installTarget === PYPI_PACKAGE_NAME
					? ['-m', 'pip', 'install', ...PIP_FLAGS, PYPI_PACKAGE_NAME]
					: ['-m', 'pip', 'install', ...PIP_FLAGS, '-e', installTarget];
				await runProvisioningStep('installing the mrd_viz backend', venvPython, installArgs, outputChannel);

				return true;
			} catch (error) {
				await reportProvisioningFailure(error, venvDir, outputChannel);
				return false;
			}
		},
	);
}

/**
 * Log the failure, remove the incomplete venv, and show a user-facing message that names the
 * step that failed and (when recognizable) hints at the cause.
 */
async function reportProvisioningFailure(error: unknown, venvDir: string, outputChannel: vscode.OutputChannel): Promise<void> {
	const step = error instanceof BackendSetupError ? error.step : undefined;
	const detail = error instanceof Error ? error.message : String(error);
	const where = step ? ` while ${step}` : '';

	outputChannel.appendLine(`Backend setup failed${where}: ${detail}`);
	await removeIncompleteVenv(venvDir, outputChannel);
	// The removed (or quarantined) venv may already be the resolver's cached selection, so drop the
	// cache defensively — otherwise a stale interpreter path could stay cached after we tore it down.
	invalidateBackendCache();
	outputChannel.show(true);

	const hint = classifyProvisioningFailure(detail);
	void vscode.window.showErrorMessage(
		`MRD Viz backend setup failed${where}: ${detail}.${hint} See the MRD Viz output channel for details, or use "Select Python Interpreter\u2026" instead.`,
	);
}

/**
 * Remove a partially built venv so retries start clean and the resolver skips a broken candidate.
 * `rm` can fail transiently (notably on Windows, where a just-exited pip may still hold a lock), so
 * retry a few times; if the directory still can't be deleted, rename it out of the way so its
 * interpreter path no longer exists (the resolver probes that path with `existsSync` and will skip
 * the candidate), then make a best-effort delete of the renamed directory.
 */
export async function removeIncompleteVenv(venvDir: string, outputChannel: Pick<vscode.OutputChannel, 'appendLine'>): Promise<void> {
	if (await tryRemoveDirectory(venvDir)) {
		outputChannel.appendLine(`Cleaned up incomplete backend environment (if present): ${venvDir}`);
		return;
	}

	const quarantineDir = `${venvDir}.broken-${Date.now()}`;
	try {
		await rename(venvDir, quarantineDir);
		outputChannel.appendLine(`Could not delete the incomplete backend environment; moved it aside to ${quarantineDir} so it will be ignored.`);
		void tryRemoveDirectory(quarantineDir);
	} catch (moveError) {
		const detail = moveError instanceof Error ? moveError.message : String(moveError);
		outputChannel.appendLine(`Warning: could not remove or move the incomplete backend environment at ${venvDir}: ${detail}`);
	}
}

/** Delete a directory tree, retrying a few times to ride out transient locks. Returns whether it is gone. */
async function tryRemoveDirectory(dir: string): Promise<boolean> {
	const attempts = 3;
	for (let attempt = 1; attempt <= attempts; attempt++) {
		try {
			await rm(dir, { recursive: true, force: true });
			return true;
		} catch {
			if (attempt === attempts) {
				return false;
			}
			await delay(attempt * 100);
		}
	}
	return false;
}

function delay(ms: number): Promise<void> {
	return new Promise(resolve => setTimeout(resolve, ms));
}

/** Map a raw failure detail to a short, actionable hint appended to the error notification. */
export function classifyProvisioningFailure(detail: string): string {
	if (/no matching distribution|could not find a version|404|not found on pypi/i.test(detail)) {
		return ' The mrd-viz package could not be found in the configured package index.';
	}
	if (/ssl|tls|proxy|connection|timed out|network|getaddrinfo|econn|temporary failure/i.test(detail)) {
		return ' This looks like a network/proxy problem reaching the package index.';
	}
	return '';
}

/** Locate a Python 3.12+ interpreter on PATH suitable for building the backend venv. */
async function findProvisioningPython(): Promise<string | undefined> {
	for (const command of PROVISIONING_PYTHON_CANDIDATES) {
		if (await isPython312OrNewer(command)) {
			return command;
		}
	}
	return undefined;
}

async function isPython312OrNewer(command: string): Promise<boolean> {
	const { error, stdout } = await runProcess(
		command,
		['-c', 'import sys; print(sys.version_info[0], sys.version_info[1])'],
		{ timeoutMs: PYTHON_VERSION_PROBE_TIMEOUT_MS },
	);
	if (error) {
		return false;
	}
	const match = /^(\d+)\s+(\d+)/.exec(stdout.trim());
	if (!match) {
		return false;
	}
	const [major, minor] = [Number(match[1]), Number(match[2])];
	return major === 3 && minor >= 12;
}

/** When running from the repo checkout, prefer an editable install of the local backend. */
function repoBackendInstallTarget(context: vscode.ExtensionContext): string | undefined {
	const backendDir = path.resolve(context.extensionUri.fsPath, '..', '..', 'backend');
	return existsSync(path.join(backendDir, 'pyproject.toml')) ? backendDir : undefined;
}

async function runProvisioningStep(step: string, command: string, args: string[], outputChannel: vscode.OutputChannel): Promise<void> {
	outputChannel.appendLine(`Running: ${command} ${args.join(' ')}`);
	const { error, stdout, stderr } = await runProcess(command, args, {
		timeoutMs: PROVISIONING_STEP_TIMEOUT_MS,
		maxBuffer: PROVISIONING_LOG_MAX_BUFFER_BYTES,
	});
	appendIfPresent(outputChannel, 'stdout', stdout);
	appendIfPresent(outputChannel, 'stderr', stderr);
	if (error) {
		const detail = (stderr.trim().split(/\r?\n/).pop() || error.message).trim();
		throw new BackendSetupError(step, detail);
	}
}

function appendIfPresent(outputChannel: vscode.OutputChannel, label: string, text: string): void {
	const trimmed = text.trim();
	if (trimmed) {
		outputChannel.appendLine(`${label}: ${trimmed}`);
	}
}

function isMrdFile(filePath: string): boolean {
	return filePath.toLowerCase().endsWith('.mrd');
}
