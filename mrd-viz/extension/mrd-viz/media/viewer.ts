// Client-side controller for the MRD Viz webview.
//
// Server-injected values arrive exclusively through the `#mrd-payload` JSON script element
// (never string-interpolated into this file), so this module can be type-checked, linted, and
// unit-tested independently of the extension host. esbuild bundles it to `media/viewer.js`.

(function () {
	const vscode = acquireVsCodeApi();
	const bootstrapElement = document.getElementById('mrd-payload');
	const bootstrap = JSON.parse((bootstrapElement && bootstrapElement.textContent) || '{}');
	const payload = bootstrap.payload || {};
	const config = bootstrap.config || {};
	let selectedIndex = null;
	let requestSequence = 0;
	let pendingRequestId = null;
	const imageCache = new Map();
	const MAX_IMAGE_CACHE_ENTRIES = Number(config.maxImageCacheEntries) || 32;

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

	function notice(text, kind?) {
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
		document.querySelectorAll<HTMLElement>('.tab').forEach(function (tab) {
			tab.addEventListener('click', function () {
				activateTab(tab.dataset.tab);
			});
		});
	}

	function activateTab(name) {
		document.querySelectorAll<HTMLElement>('.tab').forEach(function (tab) {
			tab.setAttribute('aria-selected', String(tab.dataset.tab === name));
		});
		document.querySelectorAll<HTMLElement>('.tab-panel').forEach(function (panel) {
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

	function renderSelectedTile(tile, statusText?) {
		selectedIndex = tile ? tile.image_index : null;
		document.querySelectorAll<HTMLElement>('.tile').forEach(function (node) {
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

		const responsePayload = message.payload || {};
		if (!responsePayload.ok || !responsePayload.image) {
			renderSelectedError(responsePayload.error || 'Unable to load selected image.');
			return;
		}

		const image = responsePayload.image;
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

export {};
