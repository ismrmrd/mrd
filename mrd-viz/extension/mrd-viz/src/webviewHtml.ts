import * as vscode from 'vscode';

import { redactingPayloadReplacer, type MrdOpenPayload } from './contracts';

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
					<h2 class="panel-title">Payload Summary</h2>
					<pre class="json" id="json"></pre>
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

			function valueOrUnknown(value) {
				return value === undefined || value === null || value === '' ? 'unknown' : String(value);
			}

			function formatList(value) {
				return Array.isArray(value) ? value.join('x') : '';
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
				renderSelectedTile(tile, imageCache.has(imageIndex) ? null : 'Loading full-resolution image...');
				if (!Number.isInteger(imageIndex) || imageIndex < 0 || !tile.renderable) {
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
				addField(fields, 'image_index', tile.image_index);
				addField(fields, 'stream_index', tile.stream_index);
				addField(fields, 'shape', formatList(tile.data_shape));
				addField(fields, 'rendered', formatList(tile.rendered_shape));
				addField(fields, 'dtype', tile.dtype);
				addField(fields, 'source_plane', JSON.stringify(tile.source_plane));
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
					imageCache.set(imageIndex, image);
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

function getNonce(): string {
	const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
	let text = '';
	for (let index = 0; index < 32; index += 1) {
		text += possible.charAt(Math.floor(Math.random() * possible.length));
	}

	return text;
}

export { redactingPayloadReplacer };