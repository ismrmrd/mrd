import { readFileSync } from 'node:fs';
import * as path from 'node:path';
import * as assert from 'assert';
import * as vscode from 'vscode';

import { getOpenWithMrdEditorArgs } from '../extension';
import { MRD_VIEW_TYPE } from '../mrdEditorProvider';
import { getMrdErrorHtml } from '../webviewHtml';

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
});

function readPackageJson(): ExtensionPackageJson {
	const packagePath = path.resolve(__dirname, '..', '..', 'package.json');
	return JSON.parse(readFileSync(packagePath, 'utf8')) as ExtensionPackageJson;
}
