import * as vscode from 'vscode';

const WORKFLOW_VIEW_TYPE = 'mrd-viz.workflowScaffold';

export function showWorkflowScaffoldPanel(): void {
	const panel = vscode.window.createWebviewPanel(
		WORKFLOW_VIEW_TYPE,
		'MRD Viz: Workflow View (D3 Scaffold)',
		vscode.ViewColumn.Beside,
		{
			enableScripts: false,
			retainContextWhenHidden: true,
		},
	);

	panel.webview.html = getWorkflowScaffoldHtml(panel.webview);
}

function getWorkflowScaffoldHtml(webview: vscode.Webview): string {
	const nonce = getNonce();
	const cspSource = webview.cspSource;
	return `<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'nonce-${nonce}';">
	<title>MRD Viz Workflow Scaffold</title>
	<style nonce="${nonce}">
		body {
			margin: 0;
			padding: 20px;
			font-family: var(--vscode-font-family);
			font-size: var(--vscode-font-size);
			color: var(--vscode-foreground);
			background: var(--vscode-editor-background);
			line-height: 1.45;
		}
		h1, h2 {
			margin: 0 0 8px 0;
		}
		p {
			margin: 0 0 12px 0;
			color: var(--vscode-descriptionForeground);
		}
		.grid {
			display: grid;
			gap: 12px;
			grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		}
		.card {
			border: 1px solid var(--vscode-panel-border);
			border-radius: 6px;
			padding: 10px;
			background: var(--vscode-sideBar-background);
		}
		.card h2 {
			font-size: 13px;
		}
		.card ul {
			margin: 0;
			padding-left: 18px;
			color: var(--vscode-descriptionForeground);
		}
	</style>
</head>
<body>
	<h1>D3 workflow-level view scaffold</h1>
	<p>This panel reserves product surface for session/workflow views while current file-first MRD inspection remains unchanged.</p>
	<div class="grid">
		<section class="card">
			<h2>Run timeline (placeholder)</h2>
			<ul>
				<li>Planned: run/session timeline with stage markers</li>
				<li>Planned: filter by acquisition/image/waveform events</li>
			</ul>
		</section>
		<section class="card">
			<h2>Artifact list (placeholder)</h2>
			<ul>
				<li>Planned: grouped output artifacts per run</li>
				<li>Planned: open artifact directly in MRD Viz</li>
			</ul>
		</section>
		<section class="card">
			<h2>Comparisons (placeholder)</h2>
			<ul>
				<li>Planned: compare related outputs and metadata snapshots</li>
				<li>Planned: bridge with D2 multi-file inspection flows</li>
			</ul>
		</section>
	</div>
</body>
</html>`;
}

function getNonce(): string {
	const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
	let nonce = '';
	for (let i = 0; i < 32; i += 1) {
		nonce += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
	}
	return nonce;
}
