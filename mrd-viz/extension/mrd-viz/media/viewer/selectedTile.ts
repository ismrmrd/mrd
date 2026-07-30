// The selected-tile detail panel: full-resolution image loading (with caching), per-slice controls,
// and the metadata field list.

import { state, imageCache, cacheImage } from './state';
import { notice, formatList, addField } from './dom';
import { cacheKey, buildSliceSlider, defaultSliceCoords } from './slice';
import { createImageViewport } from './viewport';
import { nextRequestId, postMessage } from './messaging';

export function selectTile(tile) {
	if (!tile) {
		state.selectedImageIndex = null;
		state.selectedTileThumb = null;
		state.selectedTileKey = null;
		state.selectedSliceDims = [];
		state.selectedSliceCoords = [];
		renderSelectedTile(null);
		return;
	}

	state.selectedImageIndex = Number(tile.image_index);
	state.selectedTileThumb = tile;
	state.selectedTileKey = tile.mosaicKey != null ? String(tile.mosaicKey) : null;
	state.selectedSliceDims = Array.isArray(tile.slice_dims) ? tile.slice_dims : [];
	state.selectedSliceCoords = defaultSliceCoords(state.selectedSliceDims, tile.source_plane);
	loadSelectedImage();
}

function loadSelectedImage() {
	const canLoad = Number.isInteger(state.selectedImageIndex)
		&& state.selectedImageIndex >= 0
		&& state.selectedTileThumb
		&& Boolean(state.selectedTileThumb.renderable);
	if (!canLoad) {
		renderSelectedTile(state.selectedTileThumb);
		return;
	}

	const key = cacheKey(state.selectedImageIndex, state.selectedSliceCoords);
	const cachedImage = imageCache.get(key);
	if (cachedImage) {
		renderSelectedTile(cachedImage, 'Loaded from selection cache.');
		return;
	}

	renderSelectedTile(state.selectedTileThumb, 'Loading full-resolution image...');
	const requestId = nextRequestId();
	state.pendingRequestId = requestId;
	state.pendingRequestIndex = state.selectedImageIndex;
	state.pendingRequestCoords = state.selectedSliceCoords.slice();
	postMessage({
		type: 'loadImage',
		requestId: requestId,
		imageIndex: state.selectedImageIndex,
		sliceCoords: state.selectedSliceCoords.slice()
	});
}

export function renderSelectedTile(tile, statusText?) {
	state.selectedIndex = tile ? tile.image_index : null;
	document.querySelectorAll<HTMLElement>('.tile').forEach(function (node) {
		node.setAttribute('aria-selected', String(state.selectedTileKey !== null && node.dataset.tileKey === state.selectedTileKey));
	});

	const root = document.getElementById('detail');
	root.textContent = '';
	if (!tile) {
		state.activeViewport = null;
		const empty = document.createElement('div');
		empty.className = 'empty';
		empty.textContent = 'No tile selected.';
		root.appendChild(empty);
		return;
	}

	if (statusText) {
		root.appendChild(notice(statusText, 'warning'));
	}

	if (tile.png_base64) {
		root.appendChild(createImageViewport(tile));
	} else {
		state.activeViewport = null;
		const frame = document.createElement('div');
		frame.className = 'selected-image';
		frame.textContent = tile.render_error || 'No image payload available.';
		root.appendChild(frame);
	}

	const sliceControls = buildSelectedSliceControls();
	if (sliceControls) {
		root.appendChild(sliceControls);
	}

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

export function handleImageLoaded(message) {
	if (message.requestId !== state.pendingRequestId) {
		return;
	}

	const responsePayload = message.payload || {};
	if (!responsePayload.ok || !responsePayload.image) {
		renderSelectedError(responsePayload.error || 'Unable to load selected image.');
		return;
	}

	const image = responsePayload.image;
	if (Number.isInteger(state.pendingRequestIndex)) {
		cacheImage(cacheKey(state.pendingRequestIndex, state.pendingRequestCoords), image);
	}

	renderSelectedTile(image);
}

function buildSelectedSliceControls() {
	if (!state.selectedSliceDims || !state.selectedSliceDims.length) {
		return null;
	}

	const wrap = document.createElement('div');
	wrap.className = 'mrd-slice-controls';
	let rendered = false;
	state.selectedSliceDims.forEach(function (dim) {
		if ((Number(dim.size) || 1) <= 1) {
			return;
		}
		rendered = true;
		wrap.appendChild(buildSliceSlider(dim, state.selectedSliceCoords[Number(dim.axis)], function (axis, value) {
			state.selectedSliceCoords[axis] = value;
			loadSelectedImage();
		}));
	});
	return rendered ? wrap : null;
}

export function renderSelectedError(error) {
	state.activeViewport = null;
	const root = document.getElementById('detail');
	root.textContent = '';
	root.appendChild(notice(error, 'error'));
}
