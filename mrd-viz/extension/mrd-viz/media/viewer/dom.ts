// Small DOM primitives and value-formatting helpers shared across the viewer modules.

export function valueOrUnknown(value) {
	return value === undefined || value === null || value === '' ? 'unknown' : String(value);
}

export function formatList(value) {
	return Array.isArray(value) ? value.join('x') : '';
}

export function stat(label, value) {
	const span = document.createElement('span');
	span.className = 'stat';
	span.textContent = label + ': ' + valueOrUnknown(value);
	return span;
}

export function notice(text, kind?) {
	const div = document.createElement('div');
	div.className = kind === 'error' ? 'notice error' : 'notice';
	div.textContent = String(text);
	return div;
}

export function section(title) {
	const root = document.createElement('section');
	root.className = 'metadata-section';
	const heading = document.createElement('h3');
	heading.textContent = title;
	root.appendChild(heading);
	return root;
}

export function addField(root, key, value) {
	const dt = document.createElement('dt');
	dt.textContent = key;
	const dd = document.createElement('dd');
	dd.textContent = valueOrUnknown(value);
	root.append(dt, dd);
}
