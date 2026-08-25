import * as vscode from 'vscode';

import { type BackendAttempt } from './backendResolver';
import { type MrdOpenPayload } from './contracts';
import { escapeHtml, getNonce, jsonForScript } from './htmlUtils';

// Maximum number of full-resolution images (base64 PNG payloads) the webview keeps in its
// in-memory LRU cache. Bounds memory when browsing many tiles: recently viewed images stay
// instant to revisit while the oldest entries are evicted. 32 comfortably covers typical
// back-and-forth navigation without letting the cache grow unbounded.
const MAX_IMAGE_CACHE_ENTRIES = 32;

export function getMrdBackendMissingHtml(webview: vscode.Webview, tried: BackendAttempt[]): string {
	const nonce = getNonce();
	const cspSource = webview.cspSource;
	// A broken developer override is a different problem from an end-user install whose bundled
	// backend won't run, so lead with the relevant explanation and primary action.
	const overrideAttempt = tried.find(attempt => attempt.kind === 'override');
	const developerOverride = overrideAttempt !== undefined;
	const intro = developerOverride
		? 'The backend configured in <code>mrdViz.backendPath</code> could not be run. It was probed with <code>--version</code> and failed for the reason shown:'
		: 'MRD Viz could not run its bundled backend on this platform. Each candidate below was probed with <code>--version</code> and failed for the reason shown:';
	const selectClass = developerOverride ? '' : 'secondary';
	const setupClass = developerOverride ? 'secondary' : '';
	const triedItems = tried.map(attempt => {
		const source = `<span class="candidate">${escapeHtml(attempt.source)}</span>`;
		const detail = attempt.detail
			? `<pre class="reason">${escapeHtml(attempt.detail)}</pre>`
			: '<div class="reason muted">No diagnostic output was captured.</div>';
		return `<li>${source}${detail}</li>`;
	}).join('');

	return `<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${cspSource} 'nonce-${nonce}'; script-src 'nonce-${nonce}';">
	<title>MRD Viz</title>
	<style nonce="${nonce}">
		* { box-sizing: border-box; }
		body {
			margin: 0;
			color: var(--vscode-foreground);
			background: var(--vscode-editor-background);
			font-family: var(--vscode-font-family);
			font-size: var(--vscode-font-size);
		}
		main { display: grid; align-content: start; gap: 12px; min-height: 100vh; padding: 24px; max-width: 820px; }
		h1 { margin: 0; font-size: 15px; font-weight: 650; }
		h2 { margin: 12px 0 0; font-size: 13px; font-weight: 600; }
		p { margin: 0; color: var(--vscode-descriptionForeground); line-height: 1.45; }
		code { font-family: var(--vscode-editor-font-family); }
		ul.candidates { margin: 4px 0; padding: 0; list-style: none; display: grid; gap: 8px; }
		ul.candidates > li {
			padding: 8px 10px;
			border: 1px solid var(--vscode-widget-border, var(--vscode-panel-border, transparent));
			border-radius: 4px;
			background: var(--vscode-textBlockQuote-background, transparent);
		}
		.candidate { display: block; font-weight: 600; overflow-wrap: anywhere; }
		.reason {
			margin: 6px 0 0;
			padding: 6px 8px;
			border-radius: 3px;
			background: var(--vscode-textCodeBlock-background, rgba(127,127,127,0.1));
			color: var(--vscode-errorForeground, var(--vscode-descriptionForeground));
			font-family: var(--vscode-editor-font-family);
			font-size: 12px;
			white-space: pre-wrap;
			overflow-wrap: anywhere;
		}
		.reason.muted { color: var(--vscode-descriptionForeground); background: none; padding: 0; margin-top: 4px; }
		pre.setup {
			margin: 4px 0 0;
			padding: 10px 12px;
			border-radius: 4px;
			background: var(--vscode-textCodeBlock-background, rgba(127,127,127,0.1));
			font-family: var(--vscode-editor-font-family);
			font-size: 12px;
			white-space: pre-wrap;
			overflow-wrap: anywhere;
		}
		.actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
		button {
			padding: 6px 12px;
			border: 1px solid var(--vscode-button-border, transparent);
			border-radius: 4px;
			color: var(--vscode-button-foreground);
			background: var(--vscode-button-background);
			font-family: inherit;
			font-size: inherit;
			cursor: pointer;
		}
		button.secondary { color: var(--vscode-button-secondaryForeground); background: var(--vscode-button-secondaryBackground); }
		button:hover { background: var(--vscode-button-hoverBackground); }
	</style>
</head>
<body>
	<main>
		<h1>MRD Viz backend not found</h1>
		<p>${intro}</p>
		<ul class="candidates">${triedItems}</ul>

		<div class="actions">
			<button type="button" id="select" class="${selectClass}">Select Python Interpreter…</button>
			<button type="button" id="setup" class="${setupClass}">Set Up Backend Automatically…</button>
		</div>

		<h2>Point MRD Viz at a Python environment</h2>
		<p>Create an environment that has the <code>mrd_viz</code> package, then set <code>mrdViz.backendPath</code> to its interpreter (or to a prebuilt <code>mrd-viz</code> binary):</p>
		<pre class="setup">python3 -m venv ~/.mrd-viz-venv
# install the backend from your mrd checkout (mrd-viz is not published to PyPI):
~/.mrd-viz-venv/bin/pip install -e path/to/mrd/mrd-viz/backend

# then set mrdViz.backendPath to:
~/.mrd-viz-venv/bin/python</pre>
		<p>Use <b>Select Python Interpreter…</b> above to browse to that interpreter (it writes <code>mrdViz.backendPath</code> for you), or <b>Set Up Backend Automatically…</b> to build a managed environment. The viewer reloads automatically once a working backend is found.</p>
		<p>You can also open this workspace in the MRD Viz dev container, which provisions the backend for you.</p>
	</main>
	<script nonce="${nonce}">
		(function () {
			const vscode = acquireVsCodeApi();
			function send(command) { vscode.postMessage({ type: 'command', command: command }); }
			document.getElementById('setup').addEventListener('click', function () { send('mrd-viz.setUpBackend'); });
			document.getElementById('select').addEventListener('click', function () { send('mrd-viz.selectInterpreter'); });
		})();
	</script>
</body>
</html>`;
}

export function getMrdViewerHtml(webview: vscode.Webview, payload: MrdOpenPayload, extensionUri: vscode.Uri): string {
	const nonce = getNonce();
	const bootstrapJson = jsonForScript({ payload, config: { maxImageCacheEntries: MAX_IMAGE_CACHE_ENTRIES } });
	const cspSource = webview.cspSource;
	const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'media', 'viewer.css'));
	const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'media', 'viewer.js'));

	return `<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${cspSource} data:; style-src ${cspSource} 'nonce-${nonce}'; script-src ${cspSource} 'nonce-${nonce}';">
	<title>MRD Viz</title>
	<link rel="stylesheet" href="${styleUri}">
</head>
<body>
	<div class="shell">
		<header class="header">
			<div class="title">
				<h1 id="title">MRD Viz</h1>
				<div class="subtitle" id="subtitle"></div>
			</div>
			<div class="stats" id="stats"></div>
		</header>
		<main class="main">
			<section class="panel" id="mosaic-panel">
				<h2 class="panel-title">Mosaic</h2>
				<div id="notices"></div>
				<div class="mosaic" id="mosaic"></div>
			</section>
			<aside class="side">
				<section class="panel" id="selected-panel">
					<h2 class="panel-title">Selected Tile</h2>
					<div class="detail" id="detail"></div>
				</section>
				<section class="panel" id="metadata-panel">
					<h2 class="panel-title">Metadata</h2>
					<div class="tabs" role="tablist" aria-label="Metadata views">
						<button class="tab" type="button" role="tab" aria-selected="true" aria-controls="metadata-groups" data-tab="groups">Groups</button>
						<button class="tab" type="button" role="tab" aria-selected="false" aria-controls="metadata-summary" data-tab="summary">Summary</button>
						<button class="tab" type="button" role="tab" aria-selected="false" aria-controls="metadata-organization" data-tab="organization">Organization</button>
						<button class="tab" type="button" role="tab" aria-selected="false" aria-controls="metadata-stream" data-tab="stream">Raw Stream</button>
						<button class="tab" type="button" role="tab" aria-selected="false" aria-controls="metadata-json" data-tab="json">Raw JSON</button>
					</div>
					<div class="tab-panel" id="metadata-groups" role="tabpanel" aria-hidden="false"></div>
					<div class="tab-panel" id="metadata-summary" role="tabpanel" aria-hidden="true"></div>
					<div class="tab-panel" id="metadata-organization" role="tabpanel" aria-hidden="true"></div>
					<div class="tab-panel" id="metadata-stream" role="tabpanel" aria-hidden="true"></div>
					<div class="tab-panel" id="metadata-json" role="tabpanel" aria-hidden="true"><pre class="json" id="json"></pre></div>
				</section>
			</aside>
		</main>
	</div>
	<script id="mrd-payload" type="application/json">${bootstrapJson}</script>
	<script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
}