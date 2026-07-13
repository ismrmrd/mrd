import * as path from 'node:path';
import * as vscode from 'vscode';

import { invalidateBackendCache } from './backendResolver';
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
		vscode.commands.registerCommand('mrd-viz.setUpBackend', () => setUpBackend()),
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

async function setUpBackend(): Promise<void> {
	const action = await vscode.window.showInformationMessage(
		'MRD Viz needs a Python 3.12 environment with the "mrd_viz" package installed. Point MRD Viz at that interpreter, or open this workspace in the MRD Viz dev container.',
		'Select Python Interpreter\u2026',
	);
	if (action) {
		await selectInterpreter();
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

	await vscode.workspace.getConfiguration('mrdViz').update('pythonPath', picked[0].fsPath, vscode.ConfigurationTarget.Global);
	invalidateBackendCache();
	void vscode.window.showInformationMessage('MRD Viz Python interpreter updated. Re-open the .mrd file to load it.');
}

function isMrdFile(filePath: string): boolean {
	return filePath.toLowerCase().endsWith('.mrd');
}

