import * as path from 'node:path';
import * as vscode from 'vscode';

export function getD3ScaffoldHtml(webview: vscode.Webview, files: readonly vscode.Uri[]): string {
	const cspSource = webview.cspSource;
	const fileItems = files.map(file => {
		const label = path.basename(file.fsPath);
		return `<li><code>${escapeHtml(label)}</code></li>`;
	}).join('');

	return `<!DOCTYPE html>
	<html lang="en">
	<head>
		<meta charset="UTF-8">
		<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'unsafe-inline'; img-src ${cspSource};">
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<title>MRD Viz Comparison Scaffold</title>
		<style>
			body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); background: var(--vscode-editor-background); padding: 24px; }
			.card { border: 1px solid var(--vscode-panel-border); border-radius: 8px; padding: 16px; max-width: 720px; }
			code { font-family: var(--vscode-editor-font-family); background: var(--vscode-textCodeBlock-background); padding: 2px 4px; border-radius: 4px; }
			ul { padding-left: 20px; }
		</style>
	</head>
	<body>
		<div class="card">
			<h1>MRD Viz D3 scaffolding</h1>
			<p>This placeholder view is the first step for the upcoming multi-file comparison experience.</p>
			<p>Selected files:</p>
			<ul>${fileItems}</ul>
			<p>Next steps for D3: add synchronized thumbnails, side-by-side metadata, and a shared selection model.</p>
		</div>
	</body>
	</html>`;
}

function escapeHtml(value: string): string {
	return value
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');
}
