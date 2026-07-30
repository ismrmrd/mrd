// Client-side controller entry point for the MRD Viz webview.
//
// Server-injected values arrive exclusively through the `#mrd-payload` JSON script element (never
// string-interpolated into these modules), so this code can be type-checked, linted, and unit-tested
// independently of the extension host. esbuild bundles this module and its imports to `media/viewer.js`.

import { state, persisted, isMaximized } from './viewer/state';
import { renderShell } from './viewer/metadata';
import { renderMosaic } from './viewer/mosaic';
import { initMessaging } from './viewer/messaging';
import { toggleMaximize } from './viewer/viewport';

initMessaging();

window.addEventListener('resize', function () {
	if (state.activeViewport) {
		state.activeViewport.refit();
	}
});

document.addEventListener('keydown', function (event) {
	const target = event.target as HTMLElement;
	if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
		return;
	}
	if (event.key === 'Escape' && isMaximized()) {
		toggleMaximize();
		return;
	}
	if (!state.activeViewport) {
		return;
	}
	if (event.key === '+' || event.key === '=') {
		state.activeViewport.zoomIn();
		event.preventDefault();
	} else if (event.key === '-' || event.key === '_') {
		state.activeViewport.zoomOut();
		event.preventDefault();
	} else if (event.key === '0') {
		state.activeViewport.fit();
		event.preventDefault();
	}
});

if (persisted.maximized) {
	document.body.classList.add('mrd-maximized');
}

renderShell();
renderMosaic();
