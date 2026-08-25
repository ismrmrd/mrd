import * as vscode from 'vscode';

import { escapeHtml, getNonce } from './htmlUtils';

export function getMrdLoadingHtml(webview: vscode.Webview, targetUri: vscode.Uri): string {
	return getMrdStateHtml(webview, 'Opening MRD file', 'Inspecting file with the MRD Viz backend.', targetUri.fsPath, '');
}

export function getMrdErrorHtml(webview: vscode.Webview, title: string, detail: string, targetPath: string): string {
	return getMrdStateHtml(webview, title, detail, targetPath, 'error');
}

function getMrdStateHtml(webview: vscode.Webview, title: string, detail: string, targetPath: string, stateClass: string): string {
	const nonce = getNonce();
	const cspSource = webview.cspSource;
	const className = stateClass ? `state ${stateClass}` : 'state';

	return `<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'nonce-${nonce}';">
	<title>MRD Viz</title>
	<style nonce="${nonce}">
		:root {
			--mrd-line: var(--vscode-panel-border);
			--mrd-text: var(--vscode-foreground);
			--mrd-muted: var(--vscode-descriptionForeground);
			--mrd-panel: var(--vscode-sideBar-background);
			--mrd-error-bg: var(--vscode-inputValidation-errorBackground);
			--mrd-error-border: var(--vscode-inputValidation-errorBorder);
		}

		* { box-sizing: border-box; }

		body {
			margin: 0;
			min-height: 100vh;
			color: var(--mrd-text);
			background: var(--vscode-editor-background);
			font-family: var(--vscode-font-family);
			font-size: var(--vscode-font-size);
		}

		.state {
			display: grid;
			align-content: center;
			gap: 8px;
			min-height: 100vh;
			padding: 24px;
		}

		.state h1 { margin: 0; font-size: 15px; font-weight: 650; }
		.state p { margin: 0; color: var(--mrd-muted); line-height: 1.45; }
		.path { overflow-wrap: anywhere; }

		.error {
			align-content: start;
		}

		.error .message {
			max-width: 760px;
			padding: 10px 12px;
			border: 1px solid var(--mrd-error-border);
			border-radius: 6px;
			background: var(--mrd-error-bg);
			color: var(--mrd-text);
		}
	</style>
</head>
<body>
	<main class="${className}">
		<h1>${escapeHtml(title)}</h1>
		<p class="message">${escapeHtml(detail)}</p>
		<p class="path">${escapeHtml(targetPath)}</p>
	</main>
</body>
</html>`;
}
