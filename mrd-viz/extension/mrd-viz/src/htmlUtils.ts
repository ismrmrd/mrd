/** Shared helpers for building webview HTML: escaping, nonces, and JSON script payloads. */

export function escapeHtml(value: string): string {
	return value.replace(/[&<>"]/g, character => {
		switch (character) {
			case '&':
				return '&amp;';
			case '<':
				return '&lt;';
			case '>':
				return '&gt;';
			case '"':
				return '&quot;';
			default:
				return character;
		}
	});
}

export function getNonce(): string {
	const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
	let text = '';
	for (let index = 0; index < 32; index += 1) {
		text += possible.charAt(Math.floor(Math.random() * possible.length));
	}

	return text;
}

export function jsonForScript(value: unknown): string {
	return JSON.stringify(value).replace(/[<>&\u2028\u2029]/g, character => {
		switch (character) {
			case '<':
				return '\\u003c';
			case '>':
				return '\\u003e';
			case '&':
				return '\\u0026';
			case '\u2028':
				return '\\u2028';
			case '\u2029':
				return '\\u2029';
			default:
				return character;
		}
	});
}
