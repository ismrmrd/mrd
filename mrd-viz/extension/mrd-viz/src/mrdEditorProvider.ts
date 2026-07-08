import * as path from 'node:path';
import * as vscode from 'vscode';

import { MrdVizBackendError, runOpenFile, type BackendRunnerOptions } from './backendRunner';
import { redactingPayloadReplacer } from './contracts';
import { getMrdErrorHtml, getMrdLoadingHtml, getMrdViewerHtml } from './webviewHtml';
import { appendIfPresent, bindViewerMessageHandling } from './viewerController';

export const MRD_VIEW_TYPE = 'mrd-viz.mrdFile';

type BackendOptionsProvider = () => BackendRunnerOptions;

class MrdDocument implements vscode.CustomDocument {
	constructor(readonly uri: vscode.Uri) {}

	dispose(): void {}
}

export class MrdEditorProvider implements vscode.CustomReadonlyEditorProvider<MrdDocument> {
	constructor(
		private readonly getBackendOptions: BackendOptionsProvider,
		private readonly outputChannel: vscode.OutputChannel,
	) {}

	openCustomDocument(uri: vscode.Uri): MrdDocument {
		return new MrdDocument(uri);
	}

	async resolveCustomEditor(
		document: MrdDocument,
		webviewPanel: vscode.WebviewPanel,
		token: vscode.CancellationToken,
	): Promise<void> {
		webviewPanel.webview.options = {
			enableScripts: true,
			localResourceRoots: [],
		};

		if (document.uri.scheme !== 'file') {
			webviewPanel.webview.html = getMrdErrorHtml(
				webviewPanel.webview,
				`Unable to open ${path.basename(document.uri.fsPath)}`,
				`MRD Viz can only open files on disk, but this resource uses the "${document.uri.scheme}" scheme.`,
				document.uri.fsPath,
			);
			return;
		}

		webviewPanel.webview.html = getMrdLoadingHtml(webviewPanel.webview, document.uri);

		const options = this.getBackendOptions();
		bindViewerMessageHandling(webviewPanel, document.uri, options, this.outputChannel);

		const abortController = new AbortController();
		const cancelSubscription = token.onCancellationRequested(() => abortController.abort());
		const disposeSubscription = webviewPanel.onDidDispose(() => abortController.abort());

		this.outputChannel.appendLine('');
		this.outputChannel.appendLine(`Running: ${formatOpenCommand(document.uri.fsPath, options)}`);

		try {
			const { payload, stderr } = await runOpenFile(document.uri.fsPath, options, abortController.signal);
			if (token.isCancellationRequested || abortController.signal.aborted) {
				return;
			}

			this.outputChannel.appendLine(JSON.stringify(payload, redactingPayloadReplacer, 2));
			appendIfPresent(this.outputChannel, 'stderr', stderr);
			webviewPanel.webview.html = getMrdViewerHtml(webviewPanel.webview, payload);
		} catch (error) {
			if (token.isCancellationRequested || abortController.signal.aborted) {
				return;
			}

			const message = error instanceof Error ? error.message : String(error);
			this.outputChannel.appendLine(`Backend failed: ${message}`);
			if (error instanceof MrdVizBackendError) {
				appendIfPresent(this.outputChannel, 'stdout', error.stdout);
				appendIfPresent(this.outputChannel, 'stderr', error.stderr);
			}
			this.outputChannel.show(true);
			webviewPanel.webview.html = getMrdErrorHtml(
				webviewPanel.webview,
				`Unable to open ${path.basename(document.uri.fsPath)}`,
				message,
				document.uri.fsPath,
			);
		} finally {
			cancelSubscription.dispose();
			disposeSubscription.dispose();
		}
	}
}

function formatOpenCommand(filePath: string, options: BackendRunnerOptions): string {
	return `${options.pythonPath} -m mrd_viz.cli open "${filePath}" --max-thumbnails ${options.maxThumbnails}`;
}
