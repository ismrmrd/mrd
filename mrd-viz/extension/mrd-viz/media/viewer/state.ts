// Shared mutable state, the VS Code API handle, the server-injected payload/config bootstrap, and
// the selection image cache.
//
// Server-injected values arrive exclusively through the `#mrd-payload` JSON script element (never
// string-interpolated), so these modules can be type-checked, linted, and unit-tested independently
// of the extension host.

export const vscode = acquireVsCodeApi();

const bootstrapElement = document.getElementById('mrd-payload');
const bootstrap = JSON.parse((bootstrapElement && bootstrapElement.textContent) || '{}');

export const payload = bootstrap.payload || {};
export const config = bootstrap.config || {};

export const persisted = (vscode.getState() || {}) as any;

// All cross-module mutable state lives in this single object so modules can share and reassign it
// without relying on live bindings.
export const state = {
	selectedIndex: null as any,
	selectedTileKey: null as any,
	requestSequence: 0,
	pendingRequestId: null as any,
	pendingRequestIndex: null as any,
	pendingRequestCoords: [] as any[],
	activeViewport: null as any,
	selectedImageIndex: null as any,
	selectedTileThumb: null as any,
	selectedSliceDims: [] as any[],
	selectedSliceCoords: [] as any[],
	mosaicMode: 'images' as string,
	mosaicRevertMode: 'images' as string,
	mosaicPending: false,
	mosaicRequestId: null as any,
	viewportHeight: Number(persisted.viewportHeight) || 0,
};

const MAX_IMAGE_CACHE_ENTRIES = Number(config.maxImageCacheEntries) || 32;

export const imageCache = new Map();

export function cacheImage(key, image) {
	if (imageCache.has(key)) {
		imageCache.delete(key);
	} else if (imageCache.size >= MAX_IMAGE_CACHE_ENTRIES) {
		const oldestKey = imageCache.keys().next().value;
		imageCache.delete(oldestKey);
	}
	imageCache.set(key, image);
}

export function isMaximized() {
	return document.body.classList.contains('mrd-maximized');
}

export function persistState() {
	vscode.setState({ viewportHeight: state.viewportHeight, maximized: isMaximized() });
}
