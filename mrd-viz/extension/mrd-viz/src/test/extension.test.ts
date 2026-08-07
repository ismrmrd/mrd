import { readFileSync, existsSync } from 'node:fs';
import { mkdir, mkdtemp, writeFile } from 'node:fs/promises';
import * as os from 'node:os';
import * as path from 'node:path';
import * as assert from 'assert';
import * as vscode from 'vscode';

import { classifyProvisioningFailure, getOpenWithMrdEditorArgs, removeIncompleteVenv } from '../extension';
import { MRD_VIEW_TYPE } from '../mrdEditorProvider';
import { planBackendCandidates } from '../backendResolver';
import { getMrdBackendMissingHtml } from '../webviewHtml';
import { getMrdErrorHtml } from '../stateHtml';
import { isViewerToExtensionMessage } from '../contracts';

interface CommandContribution {
	command: string;
	title: string;
	category?: string;
}

interface CustomEditorContribution {
	viewType: string;
	displayName: string;
	selector: Array<{ filenamePattern: string }>;
	priority?: string;
}

interface ExtensionPackageJson {
	name: string;
	contributes?: {
		commands?: CommandContribution[];
		customEditors?: CustomEditorContribution[];
	};
}

suite('MRD Viz Extension', () => {
	test('contributes MRD Viz as the default custom editor for .mrd files', () => {
		const packageJson = readPackageJson();
		const customEditor = packageJson.contributes?.customEditors?.find(editor => editor.viewType === MRD_VIEW_TYPE);

		assert.deepStrictEqual(customEditor, {
			viewType: MRD_VIEW_TYPE,
			displayName: 'MRD Viz',
			selector: [{ filenamePattern: '*.mrd' }],
			priority: 'default',
		});
	});

	test('registers the command palette entry when the extension activates', async () => {
		const extension = vscode.extensions.all.find(item => item.packageJSON.name === 'mrd-viz');
		if (!extension) {
			assert.fail('MRD Viz extension was not loaded by the VS Code test host.');
		}

		await extension.activate();
		const commands = await vscode.commands.getCommands(true);

		assert.ok(commands.includes('mrd-viz.openFile'));
		assert.ok(commands.includes('mrd-viz.setUpBackend'));
		assert.ok(commands.includes('mrd-viz.selectInterpreter'));
	});

	test('routes command opens through the custom editor view type', () => {
		const targetUri = vscode.Uri.file(path.join('sample data', 'scan.mrd'));
		const [command, uri, viewType, options] = getOpenWithMrdEditorArgs(targetUri);

		assert.strictEqual(command, 'vscode.openWith');
		assert.strictEqual(uri, targetUri);
		assert.strictEqual(viewType, MRD_VIEW_TYPE);
		assert.deepStrictEqual(options, {
			preview: false,
			viewColumn: vscode.ViewColumn.Active,
		});
	});

	test('escapes backend error details rendered inside the editor', () => {
		const webview = { cspSource: 'vscode-resource:' } as vscode.Webview;
		const html = getMrdErrorHtml(webview, 'Unable to open scan.mrd', 'Bad <script>alert("x")</script> & path', 'C:\\tmp\\scan.mrd');

		assert.ok(html.includes('Bad &lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &amp; path'));
		assert.ok(!html.includes('<script>alert'));
	});

	test('renders a guided backend-missing view with escaped candidates and failure reasons', () => {
		const webview = { cspSource: 'vscode-resource:' } as vscode.Webview;
		const html = getMrdBackendMissingHtml(webview, [
			{ source: 'development environment (<x>)', kind: 'development', detail: "No module named 'mrd_viz'" },
			{ source: 'bundled backend (/x/mrd-viz)', kind: 'bundled', detail: "libm.so.6: version `GLIBC_2.38' not found" },
		]);

		assert.ok(html.includes('MRD Viz backend not found'));
		assert.ok(html.includes('bundled backend (/x/mrd-viz)'));
		// Candidate sources are HTML-escaped.
		assert.ok(html.includes('development environment (&lt;x&gt;)'));
		// The captured probe stderr (e.g. the glibc mismatch) is surfaced and escaped.
		assert.ok(html.includes('GLIBC_2.38'));
		assert.ok(html.includes('No module named &#39;mrd_viz&#39;') || html.includes("No module named 'mrd_viz'"));
		assert.ok(html.includes('mrd-viz.setUpBackend'));
		assert.ok(html.includes('mrd-viz.selectInterpreter'));
	});

	test('tailors the backend-missing view when a developer override is broken', () => {
		const webview = { cspSource: 'vscode-resource:' } as vscode.Webview;
		const html = getMrdBackendMissingHtml(webview, [
			{ source: 'mrdViz.backendPath setting (/x/python)', kind: 'override', detail: "No module named 'mrd_viz'" },
		]);

		// The override wording leads instead of the bundled-backend wording.
		assert.ok(html.includes('configured in'));
		assert.ok(html.includes('mrdViz.backendPath'));
		assert.ok(!html.includes('could not run its bundled backend'));
	});

	test('names the legacy setting on the backend-missing page when the override came from pythonPath', () => {
		const webview = { cspSource: 'vscode-resource:' } as vscode.Webview;
		const html = getMrdBackendMissingHtml(webview, [
			{ source: 'mrdViz.pythonPath setting (/x/python)', kind: 'override', settingKey: 'mrdViz.pythonPath', detail: 'boom' },
		]);

		assert.ok(html.includes('configured in'));
		assert.ok(html.includes('mrdViz.pythonPath'));
		// The intro must not claim the value came from backendPath when it came from the legacy setting.
		assert.ok(!html.includes('<code>mrdViz.backendPath</code> could not be run'));
	});

	test('validates loadImage messages including optional slice coordinates', () => {
		assert.ok(isViewerToExtensionMessage({ type: 'loadImage', requestId: '1', imageIndex: 0 }));
		assert.ok(isViewerToExtensionMessage({ type: 'loadImage', requestId: '1', imageIndex: 2, sliceCoords: [0, 1] }));
		assert.ok(!isViewerToExtensionMessage({ type: 'loadImage', requestId: '1', imageIndex: 2, sliceCoords: [0, -1] }));
		assert.ok(!isViewerToExtensionMessage({ type: 'loadImage', requestId: '1', imageIndex: 2, sliceCoords: 'nope' }));
		assert.ok(!isViewerToExtensionMessage({ type: 'loadImage', requestId: '1', imageIndex: -1 }));
	});

	test('validates setMosaicMode messages with a known mode', () => {
		assert.ok(isViewerToExtensionMessage({ type: 'setMosaicMode', requestId: '3', mode: 'images' }));
		assert.ok(isViewerToExtensionMessage({ type: 'setMosaicMode', requestId: '3', mode: 'slices' }));
		assert.ok(!isViewerToExtensionMessage({ type: 'setMosaicMode', requestId: '3' }));
		assert.ok(!isViewerToExtensionMessage({ type: 'setMosaicMode', requestId: '3', mode: 'volumes' }));
		assert.ok(!isViewerToExtensionMessage({ type: 'nope', requestId: '3', mode: 'images' }));
	});
});

suite('MRD Viz backend provisioning', () => {
	test('hints at a missing package using the pip distribution name (mrd-viz, not mrd_viz)', () => {
		const hint = classifyProvisioningFailure('ERROR: No matching distribution found for mrd-viz');
		assert.match(hint, /mrd-viz package could not be found/);
		assert.ok(!/mrd_viz/.test(hint), 'the hint should use the pip distribution name mrd-viz, not the import name mrd_viz');
	});

	test('hints at a network/proxy problem reaching the package index', () => {
		const hint = classifyProvisioningFailure('Could not fetch URL https://pypi.org/simple/: connection timed out');
		assert.match(hint, /network\/proxy problem/);
	});

	test('returns no hint for an unrecognized failure', () => {
		assert.strictEqual(classifyProvisioningFailure('pip exited with an unexpected error'), '');
	});

	test('deletes a partially built venv so a later retry starts clean', async () => {
		const venvDir = await makeFakeVenv();
		const messages: string[] = [];
		await removeIncompleteVenv(venvDir, { appendLine: message => messages.push(message) });

		assert.ok(!existsSync(venvDir), 'the incomplete venv directory should be removed');
		assert.ok(messages.some(message => message.includes('Cleaned up incomplete backend environment')));
	});

	test('is a no-op (no throw) when the venv directory is already gone', async () => {
		const missing = path.join(os.tmpdir(), `mrd-viz-missing-${Date.now()}`);
		const messages: string[] = [];
		await removeIncompleteVenv(missing, { appendLine: message => messages.push(message) });

		assert.ok(!existsSync(missing));
		assert.ok(messages.some(message => message.includes('Cleaned up incomplete backend environment')));
	});
});

suite('MRD Viz backend resolution order', () => {
	const bundled = '/ext/media/backend/mrd-viz';
	const devVenv = '/repo/backend/.venv/bin/python';

	test('a configured override is the only candidate (no silent fallback to the bundled binary)', () => {
		const candidates = planBackendCandidates({
			configuredPath: '/custom/bin/python',
			bundledBinaryPath: bundled,
			developmentVenvPath: devVenv,
			isDevelopment: true,
		});

		assert.strictEqual(candidates.length, 1);
		assert.strictEqual(candidates[0].kind, 'override');
		assert.strictEqual(candidates[0].command, '/custom/bin/python');
		assert.deepStrictEqual(candidates[0].baseArgs, ['-m', 'mrd_viz.cli']);
	});

	test('labels the override source with the legacy setting when it came from mrdViz.pythonPath', () => {
		const [candidate] = planBackendCandidates({
			configuredPath: '/legacy/bin/python',
			configuredSettingKey: 'mrdViz.pythonPath',
			isDevelopment: false,
		});

		assert.strictEqual(candidate.kind, 'override');
		assert.strictEqual(candidate.settingKey, 'mrdViz.pythonPath');
		assert.ok(candidate.source.includes('mrdViz.pythonPath'));
	});

	test('an override pointing at the mrd-viz binary runs as a binary (no python -m args)', () => {
		const [candidate] = planBackendCandidates({ configuredPath: '/opt/mrd-viz', isDevelopment: false });

		assert.strictEqual(candidate.kind, 'override');
		assert.deepStrictEqual(candidate.baseArgs, []);
	});

	test('an unconfigured production install uses only the bundled binary', () => {
		const candidates = planBackendCandidates({
			bundledBinaryPath: bundled,
			developmentVenvPath: devVenv,
			isDevelopment: false,
		});

		assert.deepStrictEqual(candidates.map(candidate => candidate.kind), ['bundled']);
	});

	test('the development host tries the repo venv before the bundled binary', () => {
		const candidates = planBackendCandidates({
			bundledBinaryPath: bundled,
			developmentVenvPath: devVenv,
			isDevelopment: true,
		});

		assert.deepStrictEqual(candidates.map(candidate => candidate.kind), ['development', 'bundled']);
	});

	test('yields no candidates when nothing is configured, bundled, or available', () => {
		assert.deepStrictEqual(planBackendCandidates({ isDevelopment: false }), []);
	});
});

function readPackageJson(): ExtensionPackageJson {
	const packagePath = path.resolve(__dirname, '..', '..', 'package.json');
	return JSON.parse(readFileSync(packagePath, 'utf8')) as ExtensionPackageJson;
}

async function makeFakeVenv(): Promise<string> {
	const dir = await mkdtemp(path.join(os.tmpdir(), 'mrd-viz-venv-'));
	await mkdir(path.join(dir, 'bin'), { recursive: true });
	await writeFile(path.join(dir, 'bin', 'python'), '#!/bin/sh\n');
	await writeFile(path.join(dir, 'pyvenv.cfg'), 'home = /usr\n');
	return dir;
}
