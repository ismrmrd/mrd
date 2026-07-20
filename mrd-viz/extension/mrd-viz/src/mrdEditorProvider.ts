import * as path from 'node:path';
import * as vscode from 'vscode';

import { MrdVizBackendError, runOpenFile, type BackendRunnerOptions } from './backendRunner';
import { invalidateBackendCache, resolveBackend } from './backendResolver';
import { redactingPayloadReplacer } from './contracts';
import { getMrdBackendMissingHtml, getMrdViewerHtml } from './webviewHtml';
import { getMrdErrorHtml, getMrdLoadingHtml } from './stateHtml';
import { appendIfPresent, bindViewerMessageHandling } from './viewerController';

export const MRD_VIEW_TYPE = 'mrd-viz.mrdFile';

const BACKEND_SETUP_COMMANDS = new Set(['mrd-viz.setUpBackend', 'mrd-viz.selectInterpreter']);

class MrdDocument implements vscode.CustomDocument {
	constructor(readonly uri: vscode.Uri) {}

	dispose(): void {}
}

export class MrdEditorProvider implements vscode.CustomReadonlyEditorProvider<MrdDocument> {
	constructor(
		private readonly context: vscode.ExtensionContext,
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
			localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, 'media')],
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

		await this.renderDocument(document, webviewPanel, token);
	}

	private async renderDocument(
		document: MrdDocument,
		webviewPanel: vscode.WebviewPanel,
		token: vscode.CancellationToken,
	): Promise<void> {
		webviewPanel.webview.html = getMrdLoadingHtml(webviewPanel.webview, document.uri);

		const configuration = vscode.workspace.getConfiguration('mrdViz');
		const timeoutMs = configuration.get<number>('backendTimeoutMs') ?? 30000;
		const maxThumbnails = configuration.get<number>('maxThumbnails') ?? 128;

		const resolution = await resolveBackend(this.context, timeoutMs);
		if (token.isCancellationRequested) {
			return;
		}
		if (!resolution.ok) {
			this.outputChannel.appendLine('');
			this.outputChannel.appendLine('No MRD Viz backend found. Tried:');
			for (const attempt of resolution.tried) {
				this.outputChannel.appendLine(`  - ${attempt.source}`);
				const detail = attempt.detailFull ?? attempt.detail;
				if (detail) {
					for (const line of detail.split('\n')) {
						this.outputChannel.appendLine(`      ${line}`);
					}
				}
			}
			this.bindBackendSetupCommands(document, webviewPanel, token);
			webviewPanel.webview.html = getMrdBackendMissingHtml(webviewPanel.webview, resolution.tried);
			return;
		}

		const options: BackendRunnerOptions = {
			command: resolution.backend.command,
			baseArgs: resolution.backend.baseArgs,
			maxThumbnails,
			timeoutMs,
		};

		const abortController = new AbortController();
		const cancelSubscription = token.onCancellationRequested(() => abortController.abort());
		// Keep this listener for the panel's lifetime so in-flight image requests are aborted
		// when the tab is closed; VS Code disposes onDidDispose listeners after they fire.
		webviewPanel.onDidDispose(() => abortController.abort());

		bindViewerMessageHandling(webviewPanel, document.uri, options, this.outputChannel, abortController.signal);

		this.outputChannel.appendLine('');
		this.outputChannel.appendLine(`Running: ${formatOpenCommand(document.uri.fsPath, options)}`);

		try {
			const { payload, stderr } = await runOpenFile(document.uri.fsPath, options, abortController.signal);
			if (token.isCancellationRequested || abortController.signal.aborted) {
				return;
			}

			this.outputChannel.appendLine(JSON.stringify(payload, redactingPayloadReplacer, 2));
			appendIfPresent(this.outputChannel, 'stderr', stderr);
			webviewPanel.webview.html = getMrdViewerHtml(webviewPanel.webview, payload, this.context.extensionUri);
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
		}
	}

	private bindBackendSetupCommands(
		document: MrdDocument,
		webviewPanel: vscode.WebviewPanel,
		token: vscode.CancellationToken,
	): void {
		const subscription = webviewPanel.webview.onDidReceiveMessage(async (message: unknown) => {
			if (!isCommandMessage(message) || !BACKEND_SETUP_COMMANDS.has(message.command)) {
				return;
			}
			// Handle the setup action once, then re-resolve: a successful interpreter selection
			// or provisioning run should recover the viewer in place without a manual reload.
			subscription.dispose();
			await vscode.commands.executeCommand(message.command);
			if (token.isCancellationRequested) {
				return;
			}
			invalidateBackendCache();
			await this.renderDocument(document, webviewPanel, token);
		});
		webviewPanel.onDidDispose(() => subscription.dispose());
	}
}

function isCommandMessage(value: unknown): value is { type: 'command'; command: string } {
	return typeof value === 'object'
		&& value !== null
		&& (value as { type?: unknown }).type === 'command'
		&& typeof (value as { command?: unknown }).command === 'string';
}

function formatOpenCommand(filePath: string, options: BackendRunnerOptions): string {
	const parts = [options.command, ...options.baseArgs, 'open', `"${filePath}"`, '--max-thumbnails', String(options.maxThumbnails)];
	return parts.join(' ');
}
