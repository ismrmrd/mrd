// D3 metadata grouping scaffold: derive user-facing metadata sections from the existing backend
// payload so richer labels/search can evolve without changing the backend contract first.

import { formatList, valueOrUnknown } from './dom';

export interface MetadataField {
	label: string;
	value: string;
}

export interface MetadataTable {
	title: string;
	headers: string[];
	rows: string[][];
}

export interface MetadataGroup {
	id: string;
	title: string;
	description: string;
	fields: MetadataField[];
	tables: MetadataTable[];
}

export function buildMetadataGroups(payload): MetadataGroup[] {
	return [
		buildFileGroup(payload),
		buildHeaderGroup(payload),
		buildImageGroup(payload),
		buildAcquisitionGroup(payload),
		buildStreamGroup(payload),
	].filter(group => group.fields.length > 0 || group.tables.some(table => table.rows.length > 0));
}

function buildFileGroup(payload): MetadataGroup {
	return {
		id: 'file',
		title: 'File',
		description: 'Open state and high-level classification.',
		fields: [
			field('class', payload.file_class),
			field('classification reliable', payload.file_class_reliable),
			field('display mode', payload.display_mode),
			field('schema version', payload.schema_version),
			field('file size bytes', payload.file_size_bytes),
		],
		tables: (payload.warnings || []).length ? [{
			title: 'Warnings',
			headers: ['warning'],
			rows: payload.warnings.map(warning => [formatValue(warning)]),
		}] : [],
	};
}

function buildHeaderGroup(payload): MetadataGroup {
	const summary = payload.summary || {};
	return {
		id: 'header',
		title: 'Header',
		description: 'Encoding and reconstructed-space summary from the MRD header.',
		fields: [
			field('encoding count', summary.encoding_count),
			field('encoded matrix', summary.encoded_matrix),
			field('recon matrix', summary.recon_matrix),
			field('encoded FOV mm', summary.encoded_fov_mm),
			field('recon FOV mm', summary.recon_fov_mm),
		],
		tables: [],
	};
}

function buildImageGroup(payload): MetadataGroup {
	const imageItems = images(payload);
	return {
		id: 'images',
		title: 'Images',
		description: 'Image-item organization for slice/type/series scanning.',
		fields: [
			field('images', imageItems.length),
			field('unique slices', uniqueCount(imageItems.map(image => headValue(image, 'slice')))),
			field('unique image types', uniqueCount(imageItems.map(image => headValue(image, 'image_type')))),
			field('unique series', uniqueCount(imageItems.map(image => headValue(image, 'image_series_index')))),
			field('unique shapes', uniqueCount(imageItems.map(shapeKey))),
			field('unique dtypes', uniqueCount(imageItems.map(image => image.dtype))),
		],
		tables: [
			distributionTable('Slice distribution', 'slice', imageItems.map(image => headValue(image, 'slice'))),
			distributionTable('Image type distribution', 'image type', imageItems.map(image => headValue(image, 'image_type'))),
			distributionTable('Shape / dtype consistency', 'shape / dtype', imageItems.map(image => shapeKey(image) + ' / ' + formatValue(image.dtype))),
		],
	};
}

function buildAcquisitionGroup(payload): MetadataGroup {
	const acquisitionItems = acquisitions(payload);
	const firstAcquisition = acquisitionItems[0] || {};
	const idx = firstAcquisition.idx || {};
	return {
		id: 'acquisitions',
		title: 'Acquisitions',
		description: 'Raw acquisition examples and encoding counters returned by the backend.',
		fields: [
			field('examples returned', acquisitionItems.length),
			field('first stream index', firstAcquisition.stream_index),
			field('first shape', firstAcquisition.data_shape),
			field('first dtype', firstAcquisition.dtype),
			field('first flags', firstAcquisition.flags),
			field('first scan counter', firstAcquisition.scan_counter),
			field('first slice', idx.slice),
			field('first k-space step 1', idx.kspace_encode_step_1),
			field('first k-space step 2', idx.kspace_encode_step_2),
		],
		tables: [],
	};
}

function buildStreamGroup(payload): MetadataGroup {
	const stream = payload.stream || {};
	const itemRows = Object.entries(stream.item_counts || {})
		.sort(function (left, right) { return left[0].localeCompare(right[0]); })
		.map(function (entry) { return [entry[0], formatValue(entry[1])]; });

	return {
		id: 'stream',
		title: 'Stream',
		description: 'Stream item counts and metadata sample coverage.',
		fields: [
			field('images', stream.image_count),
			field('acquisitions', stream.acquisition_count),
			field('waveforms', stream.waveform_count),
			field('other items', stream.other_count),
			field('partial stream read', stream.partial),
			field('thumbnail payload truncated', payload.mosaic && payload.mosaic.truncated),
			field('returned thumbnails', payload.mosaic && payload.mosaic.thumbnails && payload.mosaic.thumbnails.length),
			field('image metadata entries', images(payload).length),
			field('acquisition examples', acquisitions(payload).length),
			field('waveform entries', waveforms(payload).length),
			field('other item entries', otherItems(payload).length),
		],
		tables: itemRows.length ? [{
			title: 'Stream item counts',
			headers: ['item type', 'count'],
			rows: itemRows,
		}] : [],
	};
}

function field(label: string, value): MetadataField {
	return { label, value: formatValue(value) };
}

function metadata(payload) {
	return payload.metadata || {};
}

function images(payload) {
	return metadata(payload).images || [];
}

function acquisitions(payload) {
	return metadata(payload).acquisitions || [];
}

function waveforms(payload) {
	return metadata(payload).waveforms || [];
}

function otherItems(payload) {
	return metadata(payload).other_items || [];
}

function headValue(image, key: string) {
	return image && image.head ? image.head[key] : undefined;
}

function shapeKey(image) {
	return formatList(image && image.data_shape) || 'unknown';
}

function distributionTable(title: string, label: string, values): MetadataTable {
	return {
		title,
		headers: [label, 'count'],
		rows: distribution(values),
	};
}

function distribution(values): string[][] {
	const counts = new Map<string, number>();
	values.forEach(function (value) {
		const key = formatValue(value);
		counts.set(key, (counts.get(key) || 0) + 1);
	});

	return Array.from(counts.entries()).sort(function (left, right) {
		return left[0].localeCompare(right[0], undefined, { numeric: true });
	}).map(function (entry) {
		return [entry[0], String(entry[1])];
	});
}

function uniqueCount(values): number {
	return distribution(values).length;
}

function formatValue(value): string {
	if (Array.isArray(value)) {
		return formatList(value);
	}
	if (value && typeof value === 'object') {
		return JSON.stringify(value);
	}
	return valueOrUnknown(value);
}
