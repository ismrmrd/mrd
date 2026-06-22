import { existsSync } from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';

import { MrdVizBackendError, runOpenFile, type BackendRunnerOptions } from './backendRunner';
import { redactingPayloadReplacer, type MrdOpenPayload } from './contracts';
import { getMrdViewerHtml } from './webviewHtml';

export function activate(context: vscode.ExtensionContext) {
	const outputChannel = vscode.window.createOutputChannel('MRD Viz');
	context.subscriptions.push(outputChannel);

	const disposable = vscode.commands.registerCommand('mrd-viz.openFile', async (resource?: vscode.Uri, selectedResources?: vscode.Uri[]) => {
		const targetUri = await resolveTargetUri(resource, selectedResources);
		if (!targetUri) {
			return;
		}

		const options = getBackendRunnerOptions(context);
		const backendCommand = `${options.pythonPath} -m mrd_viz.cli open "${targetUri.fsPath}" --max-thumbnails ${options.maxThumbnails}`;
		outputChannel.clear();
		outputChannel.appendLine(`Running: ${backendCommand}`);

		try {
			const payload = await vscode.window.withProgress(
				{
					location: vscode.ProgressLocation.Notification,
					title: 'Inspecting MRD file',
					cancellable: false,
				},
				() => runOpenFile(targetUri.fsPath, options),
			);

			outputChannel.appendLine('');
			outputChannel.appendLine(JSON.stringify(payload, redactingPayloadReplacer, 2));
			openViewerPanel(context, targetUri, payload);
			showOpenPayloadSummary(payload, outputChannel);
		} catch (error) {
			const message = error instanceof Error ? error.message : String(error);
			outputChannel.appendLine('');
			outputChannel.appendLine(`Backend failed: ${message}`);
			if (error instanceof MrdVizBackendError) {
				appendIfPresent(outputChannel, 'stdout', error.stdout);
				appendIfPresent(outputChannel, 'stderr', error.stderr);
			}
			outputChannel.show(true);
			vscode.window.showErrorMessage(`MRD Viz backend failed: ${message}`);
		}
	});

	context.subscriptions.push(disposable);
}

export function deactivate() {}

async function resolveTargetUri(resource?: vscode.Uri, selectedResources?: vscode.Uri[]): Promise<vscode.Uri | undefined> {
	if (resource?.scheme === 'file') {
		return resource;
	}

	const firstSelectedResource = selectedResources?.find(item => item.scheme === 'file');
	if (firstSelectedResource) {
		return firstSelectedResource;
	}

	const activeUri = vscode.window.activeTextEditor?.document.uri;
	if (activeUri?.scheme === 'file' && isMrdFile(activeUri.fsPath)) {
		return activeUri;
	}

	const selectedFiles = await vscode.window.showOpenDialog({
		canSelectFiles: true,
		canSelectFolders: false,
		canSelectMany: false,
		filters: {
			'MRD files': ['mrd'],
			'All files': ['*'],
		},
		openLabel: 'Inspect MRD File',
	});

	return selectedFiles?.[0];
}

function getBackendRunnerOptions(context: vscode.ExtensionContext): BackendRunnerOptions {
	const configuration = vscode.workspace.getConfiguration('mrdViz');
	const configuredPythonPath = getConfiguredPythonPath(configuration);
	return {
		pythonPath: configuredPythonPath || getDevelopmentBackendPythonPath(context.extensionPath) || 'python',
		maxThumbnails: configuration.get<number>('maxThumbnails') ?? 128,
		timeoutMs: configuration.get<number>('backendTimeoutMs') ?? 30000,
	};
}

function getConfiguredPythonPath(configuration: vscode.WorkspaceConfiguration): string | undefined {
	const inspected = configuration.inspect<string>('pythonPath');
	const value = inspected?.workspaceFolderValue ?? inspected?.workspaceValue ?? inspected?.globalValue;
	return value?.trim() || undefined;
}

function getDevelopmentBackendPythonPath(extensionPath: string): string | undefined {
	const pythonExecutable = process.platform === 'win32' ? path.join('Scripts', 'python.exe') : path.join('bin', 'python');
	const candidate = path.resolve(extensionPath, '..', '..', 'backend', '.venv', pythonExecutable);
	return existsSync(candidate) ? candidate : undefined;
}

function isMrdFile(filePath: string): boolean {
	return filePath.toLowerCase().endsWith('.mrd');
}

function showOpenPayloadSummary(payload: MrdOpenPayload, outputChannel: vscode.OutputChannel): void {
	if (!payload.ok) {
		outputChannel.show(true);
		vscode.window.showWarningMessage(`MRD Viz inspected ${payload.filename ?? 'file'}, but the backend reported an error: ${formatUnknown(payload.error)}`);
		return;
	}

	const imageCount = payload.stream?.image_count ?? 0;
	const acquisitionCount = payload.stream?.acquisition_count ?? 0;
	vscode.window.showInformationMessage(
		`MRD Viz inspected ${payload.filename ?? 'file'}: ${payload.file_class ?? 'unknown'} (${imageCount} images, ${acquisitionCount} acquisitions).`,
	);
}

function openViewerPanel(context: vscode.ExtensionContext, targetUri: vscode.Uri, payload: MrdOpenPayload): void {
	const panel = vscode.window.createWebviewPanel(
		'mrd-viz.viewer',
		`MRD Viz: ${payload.filename ?? targetUri.fsPath}`,
		vscode.ViewColumn.Beside,
		{
			enableScripts: true,
			retainContextWhenHidden: true,
		},
	);
	panel.iconPath = vscode.ThemeIcon.File;
	panel.webview.html = getMrdViewerHtml(panel.webview, payload);
	context.subscriptions.push(panel);
}

function appendIfPresent(outputChannel: vscode.OutputChannel, label: string, value: string): void {
	if (!value.trim()) {
		return;
	}

	outputChannel.appendLine('');
	outputChannel.appendLine(`${label}:`);
	outputChannel.appendLine(value);
}

function formatUnknown(value: unknown): string {
	if (typeof value === 'string') {
		return value;
	}

	if (value === undefined || value === null) {
		return 'Unknown error';
	}

	return JSON.stringify(value);
}

