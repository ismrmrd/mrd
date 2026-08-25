// postMessage helpers, request-ID sequencing, and the window 'message' listener that routes backend
// responses to the selected-tile and mosaic handlers.

import { vscode, state } from './state';
import { handleImageLoaded, renderSelectedError } from './selectedTile';
import { handleMosaicUpdated, handleMosaicError } from './mosaic';

export function nextRequestId() {
	return String(++state.requestSequence);
}

export function postMessage(message) {
	vscode.postMessage(message);
}

export function initMessaging() {
	window.addEventListener('message', function (event) {
		const message = event.data || {};
		if (message.type === 'imageLoaded') {
			handleImageLoaded(message);
		} else if (message.type === 'imageError' && message.requestId === state.pendingRequestId) {
			renderSelectedError(message.error || 'Unable to load selected image.');
		} else if (message.type === 'mosaicUpdated') {
			handleMosaicUpdated(message);
		} else if (message.type === 'mosaicError' && message.requestId === state.mosaicRequestId) {
			handleMosaicError(message.error || 'Unable to update the mosaic.');
		}
	});
}
