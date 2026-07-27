import { readFileSync } from 'node:fs';
import * as path from 'node:path';
import * as assert from 'assert';
import * as vscode from 'vscode';

import { getOpenWithMrdEditorArgs } from '../extension';
import { MRD_VIEW_TYPE } from '../mrdEditorProvider';
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
			{ source: 'bundled backend (/x/mrd-viz)', detail: "libm.so.6: version `GLIBC_2.38' not found" },
			{ source: 'mrdViz.pythonPath setting (<x>)', detail: "No module named 'mrd_viz'" },
			{ source: '"python" on PATH' },
		]);

		assert.ok(html.includes('MRD Viz backend not found'));
		assert.ok(html.includes('bundled backend (/x/mrd-viz)'));
		assert.ok(html.includes('mrdViz.pythonPath setting (&lt;x&gt;)'));
		// The captured probe stderr (e.g. the glibc mismatch) is surfaced and escaped.
		assert.ok(html.includes('GLIBC_2.38'));
		assert.ok(html.includes('No module named &#39;mrd_viz&#39;') || html.includes("No module named 'mrd_viz'"));
		assert.ok(html.includes('No diagnostic output was captured.'));
		assert.ok(html.includes('mrd-viz.setUpBackend'));
		assert.ok(html.includes('mrd-viz.selectInterpreter'));
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

function readPackageJson(): ExtensionPackageJson {
	const packagePath = path.resolve(__dirname, '..', '..', 'package.json');
	return JSON.parse(readFileSync(packagePath, 'utf8')) as ExtensionPackageJson;
}
