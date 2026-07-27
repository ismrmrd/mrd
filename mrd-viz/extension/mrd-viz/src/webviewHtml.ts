import * as vscode from 'vscode';

import { type BackendAttempt } from './backendResolver';
import { redactingPayloadReplacer, type MrdOpenPayload } from './contracts';

// Maximum number of full-resolution images (base64 PNG payloads) the webview keeps in its
// in-memory LRU cache. Bounds memory when browsing many tiles: recently viewed images stay
// instant to revisit while the oldest entries are evicted. 32 comfortably covers typical
// back-and-forth navigation without letting the cache grow unbounded.
const MAX_IMAGE_CACHE_ENTRIES = 32;

export function getMrdLoadingHtml(webview: vscode.Webview, targetUri: vscode.Uri): string {
	return getMrdStateHtml(webview, 'Opening MRD file', 'Inspecting file with the MRD Viz backend.', targetUri.fsPath, '');
}

export function getMrdErrorHtml(webview: vscode.Webview, title: string, detail: string, targetPath: string): string {
	return getMrdStateHtml(webview, title, detail, targetPath, 'error');
}

export function getMrdBackendMissingHtml(webview: vscode.Webview, tried: BackendAttempt[]): string {
	const nonce = getNonce();
	const cspSource = webview.cspSource;
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
		<p>MRD Viz needs a Python 3.12+ environment with the <code>mrd_viz</code> package installed, or the bundled standalone backend. Each candidate below was probed with <code>--version</code> and failed for the reason shown:</p>
		<ul class="candidates">${triedItems}</ul>

		<div class="actions">
			<button type="button" id="select">Select Python Interpreter…</button>
			<button type="button" id="setup" class="secondary">Set Up Backend Automatically…</button>
		</div>

		<h2>Point MRD Viz at a Python environment</h2>
		<p>Create an environment that has the <code>mrd_viz</code> package, then set <code>mrdViz.pythonPath</code> to its interpreter:</p>
		<pre class="setup">python3 -m venv ~/.mrd-viz-venv
~/.mrd-viz-venv/bin/pip install mrd-viz   # or, from a checkout: pip install -e path/to/mrd/mrd-viz/backend

# then set mrdViz.pythonPath to:
~/.mrd-viz-venv/bin/python</pre>
		<p>Use <b>Select Python Interpreter…</b> above to browse to that interpreter (it writes <code>mrdViz.pythonPath</code> for you). The viewer reloads automatically once a working backend is found.</p>
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

export function getMrdViewerHtml(webview: vscode.Webview, payload: MrdOpenPayload): string {
	const nonce = getNonce();
	const payloadJson = jsonForScript(payload);
	const cspSource = webview.cspSource;

	return `<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${cspSource} data:; style-src ${cspSource} 'nonce-${nonce}'; script-src 'nonce-${nonce}';">
	<title>MRD Viz</title>
	<style nonce="${nonce}">
		:root {
			--mrd-panel: var(--vscode-sideBar-background);
			--mrd-panel-strong: var(--vscode-editor-background);
			--mrd-line: var(--vscode-panel-border);
			--mrd-text: var(--vscode-foreground);
			--mrd-muted: var(--vscode-descriptionForeground);
			--mrd-accent: var(--vscode-focusBorder);
			--mrd-warning-bg: var(--vscode-inputValidation-warningBackground);
			--mrd-warning-border: var(--vscode-inputValidation-warningBorder);
			--mrd-error-bg: var(--vscode-inputValidation-errorBackground);
			--mrd-error-border: var(--vscode-inputValidation-errorBorder);
		}

		* { box-sizing: border-box; }

		body {
			margin: 0;
			color: var(--mrd-text);
			background: var(--vscode-editor-background);
			font-family: var(--vscode-font-family);
			font-size: var(--vscode-font-size);
		}

		button, pre { font-family: inherit; }

		.shell { min-height: 100vh; display: grid; grid-template-rows: auto minmax(0, 1fr); }

		.header {
			position: sticky;
			top: 0;
			z-index: 2;
			display: grid;
			grid-template-columns: minmax(0, 1fr) auto;
			gap: 12px;
			align-items: center;
			padding: 10px 14px;
			background: var(--mrd-panel-strong);
			border-bottom: 1px solid var(--mrd-line);
		}

		.title { min-width: 0; }

		.title h1 {
			margin: 0 0 4px;
			font-size: 15px;
			font-weight: 650;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}

		.subtitle {
			color: var(--mrd-muted);
			font-size: 12px;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}

		.stats { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }

		.stat {
			padding: 3px 7px;
			border: 1px solid var(--mrd-line);
			background: var(--mrd-panel);
			border-radius: 999px;
			color: var(--mrd-muted);
			font-size: 11px;
			white-space: nowrap;
		}

		.main {
			display: grid;
			grid-template-columns: minmax(320px, 1fr) minmax(300px, 420px);
			gap: 12px;
			padding: 12px;
			min-width: 0;
		}

		.panel {
			min-width: 0;
			border: 1px solid var(--mrd-line);
			background: var(--mrd-panel);
			border-radius: 6px;
			overflow: hidden;
		}

		.panel-title {
			margin: 0;
			padding: 9px 11px;
			border-bottom: 1px solid var(--mrd-line);
			color: var(--mrd-muted);
			font-size: 11px;
			font-weight: 650;
			letter-spacing: 0.04em;
			text-transform: uppercase;
		}

		.mosaic {
			display: grid;
			grid-template-columns: repeat(auto-fill, minmax(116px, 1fr));
			gap: 10px;
			padding: 11px;
		}

		.tile {
			display: grid;
			gap: 6px;
			width: 100%;
			min-width: 0;
			padding: 7px;
			color: inherit;
			background: var(--mrd-panel-strong);
			border: 1px solid var(--mrd-line);
			border-radius: 6px;
			cursor: pointer;
			text-align: left;
		}

		.tile:hover, .tile:focus { border-color: var(--mrd-accent); outline: none; }
		.tile[aria-selected="true"] { border-color: var(--mrd-accent); box-shadow: 0 0 0 1px var(--mrd-accent); }

		.tile img {
			width: 100%;
			aspect-ratio: 1;
			object-fit: contain;
			image-rendering: pixelated;
			background: #000;
		}

		.tile-placeholder {
			display: grid;
			place-items: center;
			width: 100%;
			aspect-ratio: 1;
			padding: 8px;
			background: var(--vscode-editor-background);
			border: 1px dashed var(--mrd-line);
			color: var(--mrd-muted);
			font-size: 11px;
			text-align: center;
		}

		.tile-name { font-size: 12px; font-weight: 650; }
		.tile-meta { color: var(--mrd-muted); font-size: 11px; overflow-wrap: anywhere; }

		.side { display: grid; gap: 12px; align-content: start; }
		.detail { display: grid; gap: 10px; padding: 11px; }

		.selected-image {
			display: grid;
			place-items: center;
			min-height: 220px;
			background: var(--vscode-editor-background);
			border: 1px solid var(--mrd-line);
			border-radius: 6px;
			color: var(--mrd-muted);
		}

		.selected-image img {
			max-width: 100%;
			max-height: 52vh;
			object-fit: contain;
			image-rendering: pixelated;
		}

		dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 4px 10px; margin: 0; font-size: 12px; }
		dt { color: var(--mrd-muted); }
		dd { margin: 0; overflow-wrap: anywhere; }
		ul { margin: 0; padding-left: 18px; }
		li + li { margin-top: 4px; }

		.notice {
			margin: 11px;
			padding: 8px 9px;
			border: 1px solid var(--mrd-warning-border);
			background: var(--mrd-warning-bg);
			border-radius: 6px;
			font-size: 12px;
		}

		.notice.error { border-color: var(--mrd-error-border); background: var(--mrd-error-bg); }
		.empty { padding: 14px; color: var(--mrd-muted); }

		.tabs {
			display: flex;
			gap: 2px;
			padding: 8px 8px 0;
			border-bottom: 1px solid var(--mrd-line);
			overflow-x: auto;
		}

		.tab {
			padding: 6px 8px;
			border: 1px solid transparent;
			border-bottom: none;
			border-radius: 5px 5px 0 0;
			color: var(--mrd-muted);
			background: transparent;
			cursor: pointer;
			font-size: 12px;
			white-space: nowrap;
		}

		.tab:hover, .tab:focus { color: var(--mrd-text); outline: none; }
		.tab[aria-selected="true"] {
			color: var(--mrd-text);
			background: var(--mrd-panel-strong);
			border-color: var(--mrd-line);
		}

		.tab-panel { display: none; padding: 11px; }
		.tab-panel[aria-hidden="false"] { display: grid; gap: 12px; }

		.metadata-section { display: grid; gap: 8px; }
		.metadata-section h3 { margin: 0; font-size: 12px; font-weight: 650; }
		.metadata-note { color: var(--mrd-muted); font-size: 12px; line-height: 1.4; }
		.metadata-table { width: 100%; border-collapse: collapse; font-size: 12px; }
		.metadata-table th,
		.metadata-table td { padding: 4px 6px; border-bottom: 1px solid var(--mrd-line); text-align: left; vertical-align: top; }
		.metadata-table th { color: var(--mrd-muted); font-weight: 500; }

		.json {
			margin: 0;
			max-height: 42vh;
			overflow: auto;
			padding: 11px;
			background: var(--vscode-textCodeBlock-background);
			font-family: var(--vscode-editor-font-family);
			font-size: 11px;
			line-height: 1.45;
			white-space: pre-wrap;
		}

		@media (max-width: 900px) {
			.header { grid-template-columns: 1fr; }
			.stats { justify-content: flex-start; }
			.main { grid-template-columns: 1fr; }
		}
	</style>
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
			<section class="panel">
				<h2 class="panel-title">Mosaic</h2>
				<div id="notices"></div>
				<div class="mosaic" id="mosaic"></div>
			</section>
			<aside class="side">
				<section class="panel">
					<h2 class="panel-title">Selected Tile</h2>
					<div class="detail" id="detail"></div>
				</section>
				<section class="panel">
					<h2 class="panel-title">Metadata</h2>
					<div class="tabs" role="tablist" aria-label="Metadata views">
						<button class="tab" type="button" role="tab" aria-selected="true" aria-controls="metadata-summary" data-tab="summary">Summary</button>
						<button class="tab" type="button" role="tab" aria-selected="false" aria-controls="metadata-organization" data-tab="organization">Organization</button>
						<button class="tab" type="button" role="tab" aria-selected="false" aria-controls="metadata-stream" data-tab="stream">Raw Stream</button>
						<button class="tab" type="button" role="tab" aria-selected="false" aria-controls="metadata-json" data-tab="json">Raw JSON</button>
					</div>
					<div class="tab-panel" id="metadata-summary" role="tabpanel" aria-hidden="false"></div>
					<div class="tab-panel" id="metadata-organization" role="tabpanel" aria-hidden="true"></div>
					<div class="tab-panel" id="metadata-stream" role="tabpanel" aria-hidden="true"></div>
					<div class="tab-panel" id="metadata-json" role="tabpanel" aria-hidden="true"><pre class="json" id="json"></pre></div>
				</section>
			</aside>
		</main>
	</div>
	<script id="mrd-payload" type="application/json">${payloadJson}</script>
	<script nonce="${nonce}">
		(function () {
			const vscode = acquireVsCodeApi();
			const payload = JSON.parse(document.getElementById('mrd-payload').textContent || '{}');
			let selectedIndex = null;
			let requestSequence = 0;
			let pendingRequestId = null;
			const imageCache = new Map();
			const MAX_IMAGE_CACHE_ENTRIES = ${MAX_IMAGE_CACHE_ENTRIES};

			function cacheImage(imageIndex, image) {
				if (imageCache.has(imageIndex)) {
					imageCache.delete(imageIndex);
				} else if (imageCache.size >= MAX_IMAGE_CACHE_ENTRIES) {
					const oldestKey = imageCache.keys().next().value;
					imageCache.delete(oldestKey);
				}
				imageCache.set(imageIndex, image);
			}

			function valueOrUnknown(value) {
				return value === undefined || value === null || value === '' ? 'unknown' : String(value);
			}

			function formatList(value) {
				return Array.isArray(value) ? value.join('x') : '';
			}

			function metadata() {
				return payload.metadata || {};
			}

			function images() {
				return metadata().images || [];
			}

			function acquisitions() {
				return metadata().acquisitions || [];
			}

			function waveforms() {
				return metadata().waveforms || [];
			}

			function otherItems() {
				return metadata().other_items || [];
			}

			function stat(label, value) {
				const span = document.createElement('span');
				span.className = 'stat';
				span.textContent = label + ': ' + valueOrUnknown(value);
				return span;
			}

			function notice(text, kind) {
				const div = document.createElement('div');
				div.className = kind === 'error' ? 'notice error' : 'notice';
				div.textContent = String(text);
				return div;
			}

			function section(title) {
				const root = document.createElement('section');
				root.className = 'metadata-section';
				const heading = document.createElement('h3');
				heading.textContent = title;
				root.appendChild(heading);
				return root;
			}

			function definitionList(entries) {
				const list = document.createElement('dl');
				entries.forEach(function (entry) {
					addField(list, entry[0], entry[1]);
				});
				return list;
			}

			function table(headers, rows) {
				const tableRoot = document.createElement('table');
				tableRoot.className = 'metadata-table';
				const thead = document.createElement('thead');
				const headerRow = document.createElement('tr');
				headers.forEach(function (header) {
					const th = document.createElement('th');
					th.textContent = header;
					headerRow.appendChild(th);
				});
				thead.appendChild(headerRow);
				tableRoot.appendChild(thead);

				const tbody = document.createElement('tbody');
				rows.forEach(function (row) {
					const tr = document.createElement('tr');
					row.forEach(function (cell) {
						const td = document.createElement('td');
						td.textContent = valueOrUnknown(cell);
						tr.appendChild(td);
					});
					tbody.appendChild(tr);
				});
				tableRoot.appendChild(tbody);
				return tableRoot;
			}

			function distribution(values) {
				const counts = new Map();
				values.forEach(function (value) {
					const key = valueOrUnknown(value);
					counts.set(key, (counts.get(key) || 0) + 1);
				});
				return Array.from(counts.entries()).sort(function (left, right) {
					return String(left[0]).localeCompare(String(right[0]), undefined, { numeric: true });
				});
			}

			function headValue(image, key) {
				return image && image.head ? image.head[key] : undefined;
			}

			function shapeKey(image) {
				return formatList(image && image.data_shape) || 'unknown';
			}

			function uniqueCount(values) {
				return distribution(values).length;
			}

			function appendEmpty(root, text) {
				const empty = document.createElement('div');
				empty.className = 'metadata-note';
				empty.textContent = text;
				root.appendChild(empty);
			}

			function redactPayload(key, value) {
				if (key === 'png_base64' && typeof value === 'string') {
					return '<base64 PNG ' + value.length + ' chars>';
				}
				return value;
			}

			function renderShell() {
				document.getElementById('title').textContent = payload.filename || 'MRD file';
				document.getElementById('subtitle').textContent = payload.path || '';

				const stats = document.getElementById('stats');
				stats.textContent = '';
				stats.append(
					stat('class', payload.file_class),
					stat('mode', payload.display_mode),
					stat('images', payload.stream && payload.stream.image_count),
					stat('acq', payload.stream && payload.stream.acquisition_count),
					stat('thumbs', payload.mosaic && payload.mosaic.thumbnails && payload.mosaic.thumbnails.length)
				);

				const notices = document.getElementById('notices');
				notices.textContent = '';
				if (!payload.ok) {
					notices.appendChild(notice(payload.error || 'The backend reported an error.', 'error'));
				}
				(payload.warnings || []).forEach(function (warning) {
					notices.appendChild(notice(warning, 'warning'));
				});
				if (payload.mosaic && payload.mosaic.truncated) {
					notices.appendChild(notice('Thumbnail payload is truncated by the configured maximum.'));
				}
				if (payload.file_class_reliable === false) {
					notices.appendChild(notice('File classification is based on a partial stream read.', 'warning'));
				}

				renderMetadata();
			}

			function renderMetadata() {
				renderSummaryMetadata();
				renderOrganizationMetadata();
				renderStreamMetadata();
				renderRawJsonMetadata();
				document.querySelectorAll('.tab').forEach(function (tab) {
					tab.addEventListener('click', function () {
						activateTab(tab.dataset.tab);
					});
				});
			}

			function activateTab(name) {
				document.querySelectorAll('.tab').forEach(function (tab) {
					tab.setAttribute('aria-selected', String(tab.dataset.tab === name));
				});
				document.querySelectorAll('.tab-panel').forEach(function (panel) {
					panel.setAttribute('aria-hidden', String(panel.id !== 'metadata-' + name));
				});
			}

			function renderSummaryMetadata() {
				const root = document.getElementById('metadata-summary');
				root.textContent = '';

				const file = section('File');
				file.appendChild(definitionList([
					['class', payload.file_class],
					['classification reliable', payload.file_class_reliable],
					['display mode', payload.display_mode],
					['schema version', payload.schema_version],
					['file size bytes', payload.file_size_bytes]
				]));
				root.appendChild(file);

				const stream = payload.stream || {};
				const counts = section('Counts');
				counts.appendChild(definitionList([
					['images', stream.image_count],
					['acquisitions', stream.acquisition_count],
					['waveforms', stream.waveform_count],
					['other items', stream.other_count],
					['returned thumbnails', payload.mosaic && payload.mosaic.thumbnails && payload.mosaic.thumbnails.length],
					['thumbnail payload truncated', payload.mosaic && payload.mosaic.truncated]
				]));
				root.appendChild(counts);

				const summary = payload.summary || {};
				const header = section('Header Summary');
				header.appendChild(definitionList([
					['encoding count', summary.encoding_count],
					['encoded matrix', formatList(summary.encoded_matrix)],
					['recon matrix', formatList(summary.recon_matrix)],
					['encoded FOV mm', formatList(summary.encoded_fov_mm)],
					['recon FOV mm', formatList(summary.recon_fov_mm)]
				]));
				root.appendChild(header);

				if ((payload.warnings || []).length) {
					const warnings = section('Warnings');
					const list = document.createElement('ul');
					payload.warnings.forEach(function (warning) {
						const item = document.createElement('li');
						item.textContent = String(warning);
						list.appendChild(item);
					});
					warnings.appendChild(list);
					root.appendChild(warnings);
				}
			}

			function renderOrganizationMetadata() {
				const root = document.getElementById('metadata-organization');
				root.textContent = '';
				const imageItems = images();
				if (!imageItems.length) {
					appendEmpty(root, 'No image metadata is available for this file.');
					return;
				}

				const overview = section('Image Set');
				overview.appendChild(definitionList([
					['images', imageItems.length],
					['unique slices', uniqueCount(imageItems.map(function (image) { return headValue(image, 'slice'); }))],
					['unique image types', uniqueCount(imageItems.map(function (image) { return headValue(image, 'image_type'); }))],
					['unique series', uniqueCount(imageItems.map(function (image) { return headValue(image, 'image_series_index'); }))],
					['unique shapes', uniqueCount(imageItems.map(shapeKey))],
					['unique dtypes', uniqueCount(imageItems.map(function (image) { return image.dtype; }))]
				]));
				root.appendChild(overview);

				const sliceRows = distribution(imageItems.map(function (image) { return headValue(image, 'slice'); }));
				const slices = section('Slice Distribution');
				slices.appendChild(table(['slice', 'image count'], sliceRows));
				root.appendChild(slices);

				const typeRows = distribution(imageItems.map(function (image) { return headValue(image, 'image_type'); }));
				const types = section('Image Type Distribution');
				types.appendChild(table(['image type', 'image count'], typeRows));
				root.appendChild(types);

				const shapeRows = distribution(imageItems.map(function (image) { return shapeKey(image) + ' / ' + valueOrUnknown(image.dtype); }));
				const shapes = section('Shape / Dtype Consistency');
				shapes.appendChild(table(['shape / dtype', 'image count'], shapeRows));
				root.appendChild(shapes);
			}

			function renderStreamMetadata() {
				const root = document.getElementById('metadata-stream');
				root.textContent = '';
				const stream = payload.stream || {};

				const itemCounts = section('Stream Item Counts');
				const rows = Object.entries(stream.item_counts || {}).sort(function (left, right) {
					return left[0].localeCompare(right[0]);
				});
				if (rows.length) {
					itemCounts.appendChild(table(['item type', 'count'], rows));
				} else {
					appendEmpty(itemCounts, 'No stream item counts were returned.');
				}
				root.appendChild(itemCounts);

				const examples = section('Metadata Examples');
				examples.appendChild(definitionList([
					['image metadata entries', images().length],
					['acquisition examples', acquisitions().length],
					['waveform entries', waveforms().length],
					['other item entries', otherItems().length]
				]));
				root.appendChild(examples);

				if (acquisitions().length) {
					const firstAcquisition = acquisitions()[0];
					const acquisition = section('First Acquisition Example');
					acquisition.appendChild(definitionList([
						['stream index', firstAcquisition.stream_index],
						['shape', formatList(firstAcquisition.data_shape)],
						['dtype', firstAcquisition.dtype],
						['flags', firstAcquisition.flags],
						['scan counter', firstAcquisition.scan_counter]
					]));
					root.appendChild(acquisition);
				}
			}

			function renderRawJsonMetadata() {
				document.getElementById('json').textContent = JSON.stringify({
					summary: payload.summary,
					stream: payload.stream,
					warnings: payload.warnings,
					metadata: payload.metadata,
					mosaic: payload.mosaic
				}, redactPayload, 2);
			}

			function renderMosaic() {
				const root = document.getElementById('mosaic');
				root.textContent = '';
				const tiles = (payload.mosaic && payload.mosaic.thumbnails) || [];
				if (!tiles.length) {
					const empty = document.createElement('div');
					empty.className = 'empty';
					empty.textContent = payload.display_mode === 'metadata_only'
						? 'No renderable image thumbnails. Metadata is available in the payload summary.'
						: 'No mosaic thumbnails were returned.';
					root.appendChild(empty);
					renderSelectedTile(null);
					return;
				}

				tiles.forEach(function (tile) {
					const button = document.createElement('button');
					button.className = 'tile';
					button.type = 'button';
					button.dataset.imageIndex = String(tile.image_index);
					button.setAttribute('aria-selected', 'false');

					if (tile.png_base64) {
						const img = document.createElement('img');
						img.src = 'data:image/png;base64,' + tile.png_base64;
						img.alt = 'MRD image item ' + valueOrUnknown(tile.image_index);
						button.appendChild(img);
					} else {
						const placeholder = document.createElement('div');
						placeholder.className = 'tile-placeholder';
						placeholder.textContent = tile.render_error || 'Not renderable';
						button.appendChild(placeholder);
					}

					const title = document.createElement('div');
					title.className = 'tile-name';
					title.textContent = 'Image ' + valueOrUnknown(tile.image_index);
					button.appendChild(title);

					const meta = document.createElement('div');
					meta.className = 'tile-meta';
					meta.textContent = formatList(tile.data_shape) + ' | stream ' + valueOrUnknown(tile.stream_index);
					button.appendChild(meta);

					button.addEventListener('click', function () {
						selectTile(tile);
					});

					root.appendChild(button);
				});

				selectTile(tiles[0]);
			}

			function selectTile(tile) {
				if (!tile) {
					renderSelectedTile(null);
					return;
				}

				const imageIndex = Number(tile.image_index);
				const canLoad = Number.isInteger(imageIndex) && imageIndex >= 0 && Boolean(tile.renderable);
				const isCached = canLoad && imageCache.has(imageIndex);
				renderSelectedTile(tile, canLoad && !isCached ? 'Loading full-resolution image...' : null);
				if (!canLoad) {
					return;
				}

				const cachedImage = imageCache.get(imageIndex);
				if (cachedImage) {
					renderSelectedTile(cachedImage, 'Loaded from selection cache.');
					return;
				}

				const requestId = String(++requestSequence);
				pendingRequestId = requestId;
				vscode.postMessage({
					type: 'loadImage',
					requestId,
					imageIndex
				});
			}

			function renderSelectedTile(tile, statusText) {
				selectedIndex = tile ? tile.image_index : null;
				document.querySelectorAll('.tile').forEach(function (node) {
					node.setAttribute('aria-selected', String(tile && String(tile.image_index) === node.dataset.imageIndex));
				});

				const root = document.getElementById('detail');
				root.textContent = '';
				if (!tile) {
					const empty = document.createElement('div');
					empty.className = 'empty';
					empty.textContent = 'No tile selected.';
					root.appendChild(empty);
					return;
				}

				if (statusText) {
					root.appendChild(notice(statusText, 'warning'));
				}

				const frame = document.createElement('div');
				frame.className = 'selected-image';
				if (tile.png_base64) {
					const img = document.createElement('img');
					img.src = 'data:image/png;base64,' + tile.png_base64;
					img.alt = 'Selected MRD image item ' + valueOrUnknown(tile.image_index);
					frame.appendChild(img);
				} else {
					frame.textContent = tile.render_error || 'No image payload available.';
				}
				root.appendChild(frame);

				const fields = document.createElement('dl');
				const head = tile.head || {};
				addField(fields, 'slice', head.slice);
				addField(fields, 'phase', head.phase);
				addField(fields, 'contrast', head.contrast);
				addField(fields, 'repetition', head.repetition);
				addField(fields, 'image type', head.image_type);
				addField(fields, 'series', head.image_series_index);
				addField(fields, 'field of view', formatList(head.field_of_view));
				addField(fields, 'image index', tile.image_index);
				addField(fields, 'stream index', tile.stream_index);
				addField(fields, 'stream item type', tile.stream_item_type);
				addField(fields, 'data shape', formatList(tile.data_shape));
				addField(fields, 'rendered shape', formatList(tile.rendered_shape));
				addField(fields, 'dtype', tile.dtype);
				addField(fields, 'source plane', JSON.stringify(tile.source_plane));
				root.appendChild(fields);
			}

			function handleImageLoaded(message) {
				if (message.requestId !== pendingRequestId) {
					return;
				}

				const payload = message.payload || {};
				if (!payload.ok || !payload.image) {
					renderSelectedError(payload.error || 'Unable to load selected image.');
					return;
				}

				const image = payload.image;
				const imageIndex = Number(image.image_index);
				if (Number.isInteger(imageIndex)) {
					cacheImage(imageIndex, image);
				}

				renderSelectedTile(image);
			}

			function renderSelectedError(error) {
				const root = document.getElementById('detail');
				root.textContent = '';
				root.appendChild(notice(error, 'error'));
			}

			function addField(root, key, value) {
				const dt = document.createElement('dt');
				dt.textContent = key;
				const dd = document.createElement('dd');
				dd.textContent = valueOrUnknown(value);
				root.append(dt, dd);
			}

			window.addEventListener('message', function (event) {
				const message = event.data || {};
				if (message.type === 'imageLoaded') {
					handleImageLoaded(message);
				} else if (message.type === 'imageError' && message.requestId === pendingRequestId) {
					renderSelectedError(message.error || 'Unable to load selected image.');
				}
			});

			renderShell();
			renderMosaic();
		})();
	</script>
</body>
</html>`;
}

function jsonForScript(value: unknown): string {
	return JSON.stringify(value).replace(/[<>&\u2028\u2029]/g, character => {
		switch (character) {
			case '<':
				return '\\u003c';
			case '>':
				return '\\u003e';
			case '&':
				return '\\u0026';
			case '\u2028':
				return '\\u2028';
			case '\u2029':
				return '\\u2029';
			default:
				return character;
		}
	});
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

function escapeHtml(value: string): string {
	return value.replace(/[&<>"]/g, character => {
		switch (character) {
			case '&':
				return '&amp;';
			case '<':
				return '&lt;';
			case '>':
				return '&gt;';
			case '"':
				return '&quot;';
			default:
				return character;
		}
	});
}

function getNonce(): string {
	const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
	let text = '';
	for (let index = 0; index < 32; index += 1) {
		text += possible.charAt(Math.floor(Math.random() * possible.length));
	}

	return text;
}

export { redactingPayloadReplacer };