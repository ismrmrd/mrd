// The interactive image surface: zoom/pan, resize, and the full-window (maximize) toggle.

import { state, persistState, isMaximized } from './state';
import { valueOrUnknown } from './dom';

function makeToolButton(label, title, onClick) {
	const button = document.createElement('button');
	button.type = 'button';
	button.className = 'mrd-tool-button';
	button.textContent = label;
	button.title = title;
	button.addEventListener('click', onClick);
	return button;
}

export function toggleMaximize() {
	document.body.classList.toggle('mrd-maximized');
	persistState();
	if (state.activeViewport) {
		if (state.activeViewport.syncControls) {
			state.activeViewport.syncControls();
		}
		requestAnimationFrame(state.activeViewport.refit);
	}
}

// Builds an interactive image surface (zoom/pan + full-window toggle) for the selected tile.
export function createImageViewport(tile) {
	const container = document.createElement('div');
	container.className = 'mrd-viewport';

	const frame = document.createElement('div');
	frame.className = 'mrd-viewport-frame';

	const img = document.createElement('img');
	img.className = 'mrd-viewport-image';
	img.src = 'data:image/png;base64,' + tile.png_base64;
	img.alt = 'Selected MRD image item ' + valueOrUnknown(tile.image_index);
	img.draggable = false;
	frame.appendChild(img);

	const MIN_SCALE = 0.05;
	const MAX_SCALE = 40;
	let scale = 1;
	let offsetX = 0;
	let offsetY = 0;
	let mode = 'fit';

	const zoomLabel = document.createElement('span');
	zoomLabel.className = 'mrd-zoom-label';

	function naturalSize() {
		return { w: img.naturalWidth || 1, h: img.naturalHeight || 1 };
	}

	function fitScale() {
		const n = naturalSize();
		const fw = frame.clientWidth || 1;
		const fh = frame.clientHeight || 1;
		return Math.min(fw / n.w, fh / n.h);
	}

	function apply() {
		img.style.transform = 'translate(' + offsetX + 'px, ' + offsetY + 'px) scale(' + scale + ')';
		zoomLabel.textContent = Math.round(scale * 100) + '%';
		frame.classList.toggle('is-pannable', scale > fitScale() + 0.0001);
	}

	function fit() {
		mode = 'fit';
		scale = fitScale();
		const n = naturalSize();
		offsetX = (frame.clientWidth - n.w * scale) / 2;
		offsetY = (frame.clientHeight - n.h * scale) / 2;
		apply();
	}

	function setScaleAbout(newScale, cx, cy) {
		newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, newScale));
		const ix = (cx - offsetX) / scale;
		const iy = (cy - offsetY) / scale;
		scale = newScale;
		offsetX = cx - ix * scale;
		offsetY = cy - iy * scale;
		apply();
	}

	function zoomBy(factor, cx, cy) {
		mode = 'free';
		setScaleAbout(scale * factor, cx, cy);
	}

	function actualSize() {
		mode = 'free';
		setScaleAbout(1, frame.clientWidth / 2, frame.clientHeight / 2);
	}

	function refit() {
		if (mode === 'fit') {
			fit();
		} else {
			apply();
		}
	}

	frame.addEventListener('wheel', function (event) {
		event.preventDefault();
		const rect = frame.getBoundingClientRect();
		const factor = event.deltaY < 0 ? 1.1 : 1 / 1.1;
		zoomBy(factor, event.clientX - rect.left, event.clientY - rect.top);
	}, { passive: false });

	let dragging = false;
	let lastX = 0;
	let lastY = 0;
	frame.addEventListener('pointerdown', function (event) {
		dragging = true;
		lastX = event.clientX;
		lastY = event.clientY;
		frame.classList.add('is-panning');
		try {
			frame.setPointerCapture(event.pointerId);
		} catch (err) { /* pointer capture is best-effort */ }
	});
	frame.addEventListener('pointermove', function (event) {
		if (!dragging) {
			return;
		}
		offsetX += event.clientX - lastX;
		offsetY += event.clientY - lastY;
		lastX = event.clientX;
		lastY = event.clientY;
		mode = 'free';
		apply();
	});
	function endDrag(event) {
		if (!dragging) {
			return;
		}
		dragging = false;
		frame.classList.remove('is-panning');
		try {
			frame.releasePointerCapture(event.pointerId);
		} catch (err) { /* pointer capture is best-effort */ }
	}
	frame.addEventListener('pointerup', endDrag);
	frame.addEventListener('pointercancel', endDrag);
	frame.addEventListener('dblclick', toggleMaximize);

	function zoomIn() {
		zoomBy(1.2, frame.clientWidth / 2, frame.clientHeight / 2);
	}

	function zoomOut() {
		zoomBy(1 / 1.2, frame.clientWidth / 2, frame.clientHeight / 2);
	}

	const maximizeButton = makeToolButton('\u2922', 'Maximize', toggleMaximize);
	maximizeButton.classList.add('mrd-tool-maximize');
	function syncMaximizeButton() {
		maximizeButton.textContent = isMaximized() ? '\u2921' : '\u2922';
		maximizeButton.title = isMaximized() ? 'Restore view (Esc)' : 'Maximize';
		maximizeButton.setAttribute('aria-label', maximizeButton.title);
	}
	syncMaximizeButton();

	const toolbar = document.createElement('div');
	toolbar.className = 'mrd-viewport-toolbar';
	toolbar.append(
		makeToolButton('\u2212', 'Zoom out (-)', zoomOut),
		zoomLabel,
		makeToolButton('+', 'Zoom in (+)', zoomIn),
		makeToolButton('Fit', 'Fit image to window (0)', fit),
		makeToolButton('1:1', 'Actual size', actualSize),
		maximizeButton
	);

	const resizer = document.createElement('div');
	resizer.className = 'mrd-viewport-resizer';
	resizer.title = 'Drag to resize the image area';
	resizer.setAttribute('aria-label', 'Resize image area');
	let resizing = false;
	let resizeStartY = 0;
	let resizeStartHeight = 0;
	resizer.addEventListener('pointerdown', function (event) {
		resizing = true;
		resizeStartY = event.clientY;
		resizeStartHeight = frame.getBoundingClientRect().height;
		try {
			resizer.setPointerCapture(event.pointerId);
		} catch (err) { /* pointer capture is best-effort */ }
		event.preventDefault();
	});
	resizer.addEventListener('pointermove', function (event) {
		if (!resizing) {
			return;
		}
		state.viewportHeight = Math.max(140, resizeStartHeight + (event.clientY - resizeStartY));
		frame.style.height = state.viewportHeight + 'px';
		refit();
	});
	function endResize(event) {
		if (!resizing) {
			return;
		}
		resizing = false;
		try {
			resizer.releasePointerCapture(event.pointerId);
		} catch (err) { /* pointer capture is best-effort */ }
		persistState();
	}
	resizer.addEventListener('pointerup', endResize);
	resizer.addEventListener('pointercancel', endResize);

	if (state.viewportHeight > 0) {
		frame.style.height = state.viewportHeight + 'px';
	}

	img.addEventListener('load', refit);
	if (img.complete && img.naturalWidth) {
		requestAnimationFrame(fit);
	}

	state.activeViewport = { refit: refit, zoomIn: zoomIn, zoomOut: zoomOut, fit: fit, syncControls: syncMaximizeButton };
	container.append(toolbar, frame, resizer);
	return container;
}
