// Header/metadata rendering: the shell (title, stats, notices), the metadata tabs, and the summary,
// organization, stream, and raw-JSON panels.

import { payload } from './state';
import { stat, notice, section, addField, valueOrUnknown, formatList } from './dom';

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

export function renderShell() {
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
