export interface MrdStreamSummary {
	item_counts?: Record<string, number>;
	image_count?: number;
	acquisition_count?: number;
	waveform_count?: number;
	other_count?: number;
}

export interface MrdMosaicTile {
	image_index?: number;
	stream_index?: number;
	stream_item_type?: string;
	data_shape?: number[];
	dtype?: string;
	png_base64?: string | null;
	rendered_shape?: number[] | null;
	thumbnail?: boolean;
	renderable?: boolean;
	render_error?: string | null;
	source_plane?: unknown;
	[key: string]: unknown;
}

export interface MrdMosaicSummary {
	tile_unit?: string;
	thumbnails?: MrdMosaicTile[];
	truncated?: boolean;
}

export interface MrdMetadataSummary {
	images?: unknown[];
	acquisitions?: unknown[];
	waveforms?: unknown[];
	other_items?: unknown[];
	[key: string]: unknown;
}

export interface MrdOpenPayload {
	ok: boolean;
	schema_version?: number;
	path?: string;
	filename?: string;
	file_size_bytes?: number | null;
	file_class?: string;
	file_class_reliable?: boolean;
	display_mode?: string;
	summary?: Record<string, unknown>;
	stream?: MrdStreamSummary;
	mosaic?: MrdMosaicSummary;
	metadata?: MrdMetadataSummary;
	warnings?: unknown[];
	error?: unknown;
	[key: string]: unknown;
}

export function isMrdOpenPayload(value: unknown): value is MrdOpenPayload {
	return typeof value === 'object'
		&& value !== null
		&& 'ok' in value
		&& typeof (value as { ok: unknown }).ok === 'boolean';
}

export function redactingPayloadReplacer(key: string, value: unknown): unknown {
	if (key === 'png_base64' && typeof value === 'string') {
		return `<base64 PNG ${value.length} chars>`;
	}

	return value;
}

export type MrdImagePayload = MrdMosaicTile;

export interface MrdImageResponsePayload {
	ok: boolean;
	path?: string;
	filename?: string;
	file_class?: string;
	display_mode?: string;
	image?: MrdImagePayload;
	error?: unknown;
	[key: string]: unknown;
}

export interface LoadImageRequestMessage {
	type: 'loadImage';
	requestId: string;
	imageIndex: number;
}

export interface ImageLoadedMessage {
	type: 'imageLoaded';
	requestId: string;
	payload: MrdImageResponsePayload;
}

export interface ImageErrorMessage {
	type: 'imageError';
	requestId: string;
	imageIndex: number;
	error: string;
}

export type ViewerToExtensionMessage = LoadImageRequestMessage;

export type ExtensionToViewerMessage = ImageLoadedMessage | ImageErrorMessage;

export function isMrdImageResponsePayload(value: unknown): value is MrdImageResponsePayload {
	return typeof value === 'object'
		&& value !== null
		&& 'ok' in value
		&& typeof (value as { ok: unknown }).ok === 'boolean';
}

export function isViewerToExtensionMessage(value: unknown): value is ViewerToExtensionMessage {
	if (typeof value !== 'object' || value === null) {
		return false;
	}

	const message = value as { type?: unknown; requestId?: unknown; imageIndex?: unknown };
	const imageIndex = message.imageIndex;
	return message.type === 'loadImage'
		&& typeof message.requestId === 'string'
		&& typeof imageIndex === 'number'
		&& Number.isInteger(imageIndex)
		&& imageIndex >= 0;
}