// Slice-coordinate math, image cache keys, and the per-axis slider control.

export function clampIndex(value, size) {
	const numeric = Number.isInteger(value) ? value : Number(value) || 0;
	return Math.max(0, Math.min(numeric, size - 1));
}

export function defaultSliceCoords(dims, sourcePlane) {
	const coords = [];
	(dims || []).forEach(function (dim) {
		const axis = Number(dim.axis);
		let value = 0;
		if (sourcePlane && typeof sourcePlane === 'object' && dim.name in sourcePlane) {
			value = Number(sourcePlane[dim.name]) || 0;
		}
		coords[axis] = clampIndex(value, Number(dim.size) || 1);
	});
	return coords;
}

export function cacheKey(imageIndex, coords) {
	return String(imageIndex) + '@' + (coords || []).join(',');
}

export function buildSliceSlider(dim, currentValue, onCommit) {
	const size = Number(dim.size) || 1;
	const axis = Number(dim.axis);
	const label = dim.name || ('axis ' + axis);
	const current = clampIndex(currentValue, size);

	const row = document.createElement('div');
	row.className = 'mrd-slice-row';

	const caption = document.createElement('span');
	caption.className = 'mrd-slice-name';
	caption.textContent = label + ' ' + current + ' / ' + (size - 1);

	const slider = document.createElement('input');
	slider.type = 'range';
	slider.min = '0';
	slider.max = String(size - 1);
	slider.step = '1';
	slider.value = String(current);
	slider.setAttribute('aria-label', 'Step ' + label);
	slider.addEventListener('input', function () {
		caption.textContent = label + ' ' + slider.value + ' / ' + (size - 1);
	});
	slider.addEventListener('change', function () {
		onCommit(axis, Number(slider.value));
	});

	row.append(caption, slider);
	return row;
}
