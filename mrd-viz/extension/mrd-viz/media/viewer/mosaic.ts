// The thumbnail mosaic: tile buttons, the images/slices view toggle, and mosaic-update handling.

import { state, payload } from './state';
import { notice, formatList, valueOrUnknown } from './dom';
import { selectTile, renderSelectedTile } from './selectedTile';
import { nextRequestId, postMessage } from './messaging';

export function renderMosaic() {
	const root = document.getElementById('mosaic');
	root.textContent = '';
	removeMosaicModeControls();
	const tiles = currentTiles();
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

	tiles.forEach(function (tile, tileIndex) {
		tile.mosaicKey = tileIndex;
		const button = document.createElement('button');
		button.className = 'tile';
		button.type = 'button';
		button.dataset.imageIndex = String(tile.image_index);
		button.dataset.tileKey = String(tileIndex);
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
		title.textContent = tile.tile_title || ('Image ' + valueOrUnknown(tile.image_index));
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

	renderMosaicModeControls(tiles);
	selectTile(tiles[0]);
}

function currentTiles() {
	// The host forwards backend output; guard against a non-array `thumbnails` (e.g. from an
	// incompatible or corrupted backend) so `.length`/`.forEach` below cannot throw and blank
	// the editor.
	const tiles = payload.mosaic && payload.mosaic.thumbnails;
	return Array.isArray(tiles) ? tiles : [];
}

function removeMosaicModeControls() {
	const existing = document.getElementById('mosaic-mode');
	if (existing) {
		existing.remove();
	}
}

function mosaicCanExplode(tiles) {
	return tiles.some(function (tile) {
		const dims = tile && tile.slice_dims;
		if (!Array.isArray(dims) || !dims.length) {
			return false;
		}
		const z = dims[dims.length - 1];
		return Boolean(z) && (Number(z.size) || 1) > 1;
	});
}

function setMosaicNotice(text, kind) {
	const noticesEl = document.getElementById('notices');
	if (!noticesEl) {
		return;
	}
	// Manage only our own status node so backend error/warning notices from renderShell() survive.
	const existing = document.getElementById('mosaic-status');
	if (existing) {
		existing.remove();
	}
	if (text) {
		const node = notice(text, kind);
		node.id = 'mosaic-status';
		noticesEl.appendChild(node);
	}
}

function makeMosaicModeButton(mode, label, title) {
	const button = document.createElement('button');
	button.type = 'button';
	button.className = 'mrd-segmented-button';
	button.textContent = label;
	button.title = title;
	if (state.mosaicMode === mode) {
		button.classList.add('is-active');
	}
	button.setAttribute('aria-pressed', state.mosaicMode === mode ? 'true' : 'false');
	button.disabled = state.mosaicPending;
	button.addEventListener('click', function () {
		setMosaicMode(mode);
	});
	return button;
}

function renderMosaicModeControls(tiles) {
	removeMosaicModeControls();
	if (!mosaicCanExplode(tiles)) {
		return;
	}

	const bar = document.createElement('div');
	bar.id = 'mosaic-mode';
	bar.className = 'mrd-mosaic-mode';

	const label = document.createElement('span');
	label.className = 'mrd-mosaic-mode-label';
	label.textContent = 'View';
	bar.appendChild(label);

	const group = document.createElement('div');
	group.className = 'mrd-segmented';
	group.setAttribute('role', 'group');
	group.append(
		makeMosaicModeButton('images', 'Images', 'One thumbnail per image'),
		makeMosaicModeButton('slices', 'Slices', 'One thumbnail per z slice')
	);
	bar.appendChild(group);

	const mosaicEl = document.getElementById('mosaic');
	mosaicEl.parentNode.insertBefore(bar, mosaicEl);
}

function setMosaicMode(mode) {
	if (state.mosaicPending || mode === state.mosaicMode) {
		return;
	}
	state.mosaicRevertMode = state.mosaicMode;
	state.mosaicMode = mode;
	state.mosaicPending = true;
	const requestId = nextRequestId();
	state.mosaicRequestId = requestId;
	renderMosaicModeControls(currentTiles());
	setMosaicNotice(mode === 'slices' ? 'Rendering individual slices...' : 'Rebuilding image mosaic...', 'warning');
	postMessage({
		type: 'setMosaicMode',
		requestId: requestId,
		mode: mode
	});
}

export function handleMosaicUpdated(message) {
	if (message.requestId !== state.mosaicRequestId) {
		return;
	}

	state.mosaicPending = false;
	const responsePayload = message.payload || {};
	if (responsePayload.ok !== true || !responsePayload.mosaic) {
		handleMosaicError((responsePayload && responsePayload.error) || 'Unable to update the mosaic.');
		return;
	}

	payload.mosaic = responsePayload.mosaic;
	setMosaicNotice('', null);
	renderMosaic();
}

export function handleMosaicError(error) {
	state.mosaicPending = false;
	state.mosaicMode = state.mosaicRevertMode;
	setMosaicNotice(String(error), 'error');
	renderMosaicModeControls(currentTiles());
}
