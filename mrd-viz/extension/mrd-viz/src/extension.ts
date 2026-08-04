import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, rename, rm } from 'node:fs/promises';
import * as path from 'node:path';
import * as vscode from 'vscode';

import { invalidateBackendCache, managedVenvDirectory, managedVenvPythonPath } from './backendResolver';
import { MrdEditorProvider, MRD_VIEW_TYPE } from './mrdEditorProvider';

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
		vscode.workspace.onDidChangeConfiguration(event => {
			if (event.affectsConfiguration('mrdViz.pythonPath')) {
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
	const proceed = await vscode.window.showInformationMessage(
		'Set up the MRD Viz backend automatically? This creates a private Python virtual environment in the extension\u2019s storage and installs the "mrd_viz" package with pip. It needs a Python 3.12+ interpreter on PATH and network access.',
		{ modal: true },
		'Install',
	);
	if (proceed !== 'Install') {
		return;
	}

	const installed = await provisionManagedBackend(context, outputChannel);
	if (installed) {
		invalidateBackendCache();
		void vscode.window.showInformationMessage('MRD Viz backend installed.');
	}
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

	const config = vscode.workspace.getConfiguration('mrdViz');
	await config.update('pythonPath', picked[0].fsPath, vscode.ConfigurationTarget.Global);
	// Clear any narrower-scoped values (e.g. a dev container's workspace-level setting) that would
	// otherwise shadow the interpreter the user just picked and block recovery via the guided flow.
	const inspected = config.inspect<string>('pythonPath');
	if (inspected?.workspaceFolderValue !== undefined) {
		await config.update('pythonPath', undefined, vscode.ConfigurationTarget.WorkspaceFolder);
	}
	if (inspected?.workspaceValue !== undefined) {
		await config.update('pythonPath', undefined, vscode.ConfigurationTarget.Workspace);
	}
	invalidateBackendCache();
	void vscode.window.showInformationMessage('MRD Viz Python interpreter updated.');
}

/** A provisioning step that failed, tagged with the human-readable phase for clear reporting. */
class BackendSetupError extends Error {
	constructor(readonly step: string, detail: string) {
		super(detail);
		this.name = 'BackendSetupError';
	}
}

/**
 * Provision the managed backend virtual environment (resolver candidate #3) in global storage:
 * create a venv from a discovered Python 3.12+ interpreter and `pip install` the backend. Returns
 * true only if every step succeeds; on any failure the half-provisioned venv is removed (so a
 * stale interpreter can't satisfy the resolver probe and then fail at `import mrd_viz`) and the
 * cause is surfaced to the user and the output channel.
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
	const installTarget = repoBackendInstallTarget(context) ?? 'mrd-viz';

	return vscode.window.withProgress(
		{ location: vscode.ProgressLocation.Notification, title: 'Setting up MRD Viz backend', cancellable: false },
		async progress => {
			try {
				await mkdir(path.dirname(venvDir), { recursive: true });

				progress.report({ message: 'Creating virtual environment\u2026' });
				await runProvisioningStep('creating the virtual environment', basePython, ['-m', 'venv', venvDir], outputChannel);

				progress.report({ message: 'Upgrading pip\u2026' });
				await runProvisioningStep('upgrading pip', venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip'], outputChannel);

				progress.report({ message: 'Installing the mrd_viz backend\u2026' });
				const installArgs = installTarget === 'mrd-viz'
					? ['-m', 'pip', 'install', 'mrd-viz']
					: ['-m', 'pip', 'install', '-e', installTarget];
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
	for (const command of ['python3.12', 'python3', 'python']) {
		if (await isPython312OrNewer(command)) {
			return command;
		}
	}
	return undefined;
}

function isPython312OrNewer(command: string): Promise<boolean> {
	return new Promise(resolve => {
		execFile(
			command,
			['-c', 'import sys; print(sys.version_info[0], sys.version_info[1])'],
			{ timeout: 10000, windowsHide: true },
			(error, stdout) => {
				if (error) {
					resolve(false);
					return;
				}
				const match = /^(\d+)\s+(\d+)/.exec(stdout.trim());
				if (!match) {
					resolve(false);
					return;
				}
				const [major, minor] = [Number(match[1]), Number(match[2])];
				resolve(major === 3 && minor >= 12);
			},
		);
	});
}

/** When running from the repo checkout, prefer an editable install of the local backend. */
function repoBackendInstallTarget(context: vscode.ExtensionContext): string | undefined {
	const backendDir = path.resolve(context.extensionUri.fsPath, '..', '..', 'backend');
	return existsSync(path.join(backendDir, 'pyproject.toml')) ? backendDir : undefined;
}

function runProvisioningStep(step: string, command: string, args: string[], outputChannel: vscode.OutputChannel): Promise<void> {
	outputChannel.appendLine(`Running: ${command} ${args.join(' ')}`);
	return new Promise((resolve, reject) => {
		execFile(command, args, { timeout: 600000, windowsHide: true, maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
			appendIfPresent(outputChannel, 'stdout', stdout);
			appendIfPresent(outputChannel, 'stderr', stderr);
			if (error) {
				const detail = (stderr.trim().split(/\r?\n/).pop() || error.message).trim();
				reject(new BackendSetupError(step, detail));
				return;
			}
			resolve();
		});
	});
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

