import { existsSync } from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';

import type { BackendRunnerOptions } from './backendRunner';
import { MrdEditorProvider, MRD_VIEW_TYPE } from './mrdEditorProvider';

export function activate(context: vscode.ExtensionContext) {
	const outputChannel = vscode.window.createOutputChannel('MRD Viz');
	context.subscriptions.push(outputChannel);

	const editorProvider = new MrdEditorProvider(() => getBackendRunnerOptions(context), outputChannel);
	context.subscriptions.push(vscode.window.registerCustomEditorProvider(MRD_VIEW_TYPE, editorProvider, {
		webviewOptions: {
			retainContextWhenHidden: true,
		},
	}));

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

