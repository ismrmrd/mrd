import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir } from 'node:fs/promises';
import * as path from 'node:path';
import * as vscode from 'vscode';

import { getConfiguredPythonPath } from './backendResolver';

const MIN_PYTHON_MAJOR = 3;
const MIN_PYTHON_MINOR = 12;
const FALLBACK_GIT_INSTALL = 'git+https://github.com/ismrmrd/mrd.git#subdirectory=mrd-viz/backend';

export type BackendInstallSource =
	| { kind: 'auto' }
	| { kind: 'wheel'; wheelPath: string };

export class BackendSetupError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'BackendSetupError';
	}
}

interface CommandResult {
	stdout: string;
	stderr: string;
}

export async function provisionManagedBackend(
	context: vscode.ExtensionContext,
	outputChannel: vscode.OutputChannel,
	installSource: BackendInstallSource,
): Promise<string> {
	const bootstrapPython = await resolveBootstrapPython(outputChannel);
	const venvRoot = path.join(context.globalStorageUri.fsPath, 'backend-venv');
	const venvPython = path.join(venvRoot, pythonExecutableRelative());

	await mkdir(context.globalStorageUri.fsPath, { recursive: true });

	if (!existsSync(venvPython)) {
		await runCommand(
			bootstrapPython,
			['-m', 'venv', venvRoot],
			outputChannel,
			'Creating managed backend virtual environment',
		);
	}

	await runCommand(
		venvPython,
		['-m', 'pip', 'install', '--upgrade', 'pip'],
		outputChannel,
		'Updating pip in managed backend virtual environment',
	);

	if (installSource.kind === 'wheel') {
		await runCommand(
			venvPython,
			['-m', 'pip', 'install', '--upgrade', installSource.wheelPath],
			outputChannel,
			`Installing backend from wheel (${installSource.wheelPath})`,
		);
	} else {
		try {
			await runCommand(
				venvPython,
				['-m', 'pip', 'install', '--upgrade', 'mrd-viz'],
				outputChannel,
				'Installing backend from PyPI (mrd-viz)',
			);
		} catch (error) {
			outputChannel.appendLine('PyPI install failed; falling back to GitHub source install.');
			await runCommand(
				venvPython,
				['-m', 'pip', 'install', '--upgrade', FALLBACK_GIT_INSTALL],
				outputChannel,
				`Installing backend from GitHub (${FALLBACK_GIT_INSTALL})`,
			);
			if (error instanceof Error) {
				outputChannel.appendLine(`PyPI error detail: ${error.message}`);
			}
		}
	}

	await runCommand(
		venvPython,
		['-m', 'mrd_viz.cli', '--version'],
		outputChannel,
		'Validating managed backend CLI',
	);

	return venvPython;
}

async function resolveBootstrapPython(outputChannel: vscode.OutputChannel): Promise<string> {
	const tried: string[] = [];
	const commands = uniqueCommands([getConfiguredPythonPath(), 'python3', 'python']);
	for (const command of commands) {
		try {
			const result = await runCommand(
				command,
				['-c', 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")'],
				outputChannel,
				`Probing Python interpreter (${command})`,
			);
			const versionText = result.stdout.trim().split(/\r?\n/).at(-1) ?? '';
			const [majorText, minorText] = versionText.split('.');
			const major = Number(majorText);
			const minor = Number(minorText);
			if (Number.isInteger(major) && Number.isInteger(minor) && (major > MIN_PYTHON_MAJOR || (major === MIN_PYTHON_MAJOR && minor >= MIN_PYTHON_MINOR))) {
				return command;
			}
			tried.push(`${command} (found ${versionText || 'unknown version'})`);
		} catch (error) {
			const detail = error instanceof Error ? error.message : String(error);
			tried.push(`${command} (${detail})`);
		}
	}

	throw new BackendSetupError(
		`Could not find a usable Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ interpreter. Tried: ${tried.join('; ')}`,
	);
}

function uniqueCommands(values: Array<string | undefined>): string[] {
	const commands: string[] = [];
	const seen = new Set<string>();
	for (const value of values) {
		const trimmed = value?.trim();
		if (!trimmed || seen.has(trimmed)) {
			continue;
		}
		seen.add(trimmed);
		commands.push(trimmed);
	}
	return commands;
}

function runCommand(
	command: string,
	args: string[],
	outputChannel: vscode.OutputChannel,
	label: string,
): Promise<CommandResult> {
	outputChannel.appendLine('');
	outputChannel.appendLine(`MRD Viz setup: ${label}`);
	outputChannel.appendLine(`Running: ${[command, ...args].join(' ')}`);

	return new Promise((resolve, reject) => {
		execFile(command, args, { windowsHide: true }, (error, stdout, stderr) => {
			const result = { stdout, stderr };
			appendIfPresent(outputChannel, 'stdout', stdout);
			appendIfPresent(outputChannel, 'stderr', stderr);
			if (error) {
				reject(new BackendSetupError(`${label} failed: ${error.message}`));
				return;
			}
			resolve(result);
		});
	});
}

function appendIfPresent(outputChannel: vscode.OutputChannel, stream: 'stdout' | 'stderr', content: string): void {
	const trimmed = content.trim();
	if (trimmed.length === 0) {
		return;
	}
	outputChannel.appendLine(`${stream}:`);
	outputChannel.appendLine(trimmed);
}

function pythonExecutableRelative(): string {
	return process.platform === 'win32' ? path.join('Scripts', 'python.exe') : path.join('bin', 'python');
}
