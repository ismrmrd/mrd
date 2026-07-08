import * as vscode from 'vscode';

import { MrdVizBackendError, runImage, type BackendRunnerOptions } from './backendRunner';
import { isViewerToExtensionMessage, type ExtensionToViewerMessage } from './contracts';

interface ViewerPanelLike {
	readonly webview: vscode.Webview;
	onDidDispose(listener: () => unknown): vscode.Disposable;
}

export function bindViewerMessageHandling(
	panel: ViewerPanelLike,
	targetUri: vscode.Uri,
	options: BackendRunnerOptions,
	outputChannel: vscode.OutputChannel,
	signal: AbortSignal,
): vscode.Disposable {
	const messageSubscription = panel.webview.onDidReceiveMessage(message => {
		void handleViewerMessage(panel.webview, targetUri, options, outputChannel, signal, message);
	});
	const disposeSubscription = panel.onDidDispose(() => messageSubscription.dispose());
	return vscode.Disposable.from(messageSubscription, disposeSubscription);
}

async function handleViewerMessage(
	webview: vscode.Webview,
	targetUri: vscode.Uri,
	options: BackendRunnerOptions,
	outputChannel: vscode.OutputChannel,
	signal: AbortSignal,
	message: unknown,
): Promise<void> {
	if (!isViewerToExtensionMessage(message)) {
		outputChannel.appendLine('Ignored malformed MRD Viz webview message.');
		return;
	}

	try {
		const { payload, stderr } = await runImage(targetUri.fsPath, message.imageIndex, options, signal);
		appendIfPresent(outputChannel, 'stderr', stderr);
		postViewerMessage(webview, {
			type: 'imageLoaded',
			requestId: message.requestId,
			payload,
		});
	} catch (error) {
		if (signal.aborted) {
			return;
		}

		const errorMessage = error instanceof Error ? error.message : String(error);
		outputChannel.appendLine(`Selected image ${message.imageIndex} failed: ${errorMessage}`);
		if (error instanceof MrdVizBackendError) {
			appendIfPresent(outputChannel, 'stdout', error.stdout);
			appendIfPresent(outputChannel, 'stderr', error.stderr);
		}
		postViewerMessage(webview, {
			type: 'imageError',
			requestId: message.requestId,
			imageIndex: message.imageIndex,
			error: errorMessage,
		});
	}
}

function postViewerMessage(webview: vscode.Webview, message: ExtensionToViewerMessage): void {
	void webview.postMessage(message);
}

export function appendIfPresent(outputChannel: vscode.OutputChannel, label: string, value: string): void {
	if (!value.trim()) {
		return;
	}

	outputChannel.appendLine('');
	outputChannel.appendLine(`${label}:`);
	outputChannel.appendLine(value);
}
