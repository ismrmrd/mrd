import { execFile } from 'node:child_process';

import { isMrdImageResponsePayload, isMrdOpenPayload, type MrdImageResponsePayload, type MrdOpenPayload } from './contracts';

export interface BackendRunnerOptions {
	pythonPath: string;
	maxThumbnails: number;
	timeoutMs: number;
}

export class MrdVizBackendError extends Error {
	constructor(
		message: string,
		readonly stdout: string,
		readonly stderr: string,
	) {
		super(message);
		this.name = 'MrdVizBackendError';
	}
}

export async function runOpenFile(filePath: string, options: BackendRunnerOptions): Promise<MrdOpenPayload> {
	const commandArguments = [
		'-m',
		'mrd_viz.cli',
		'open',
		filePath,
		'--max-thumbnails',
		String(options.maxThumbnails),
	];
	const result = await execPython(options.pythonPath, commandArguments, options.timeoutMs);
	return parseOpenPayload(result.stdout);
}

export async function runImage(filePath: string, imageIndex: number, options: BackendRunnerOptions): Promise<MrdImageResponsePayload> {
	const commandArguments = [
		'-m',
		'mrd_viz.cli',
		'image',
		filePath,
		'--index',
		String(imageIndex),
	];
	const result = await execPython(options.pythonPath, commandArguments, options.timeoutMs);
	return parseImagePayload(result.stdout);
}

function execPython(pythonPath: string, commandArguments: string[], timeoutMs: number): Promise<{ stdout: string; stderr: string }> {
	return new Promise((resolve, reject) => {
		execFile(
			pythonPath,
			commandArguments,
			{
				maxBuffer: 64 * 1024 * 1024,
				timeout: timeoutMs,
				windowsHide: true,
			},
			(error, stdout, stderr) => {
				const stdoutText = stdout.toString();
				const stderrText = stderr.toString();
				if (error && !stdoutText.trim()) {
					reject(new MrdVizBackendError(error.message, stdoutText, stderrText));
					return;
				}

				resolve({ stdout: stdoutText, stderr: stderrText });
			},
		);
	});
}

function parseOpenPayload(stdout: string): MrdOpenPayload {
	return parsePayload(stdout, isMrdOpenPayload, 'open-file');
}

function parseImagePayload(stdout: string): MrdImageResponsePayload {
	return parsePayload(stdout, isMrdImageResponsePayload, 'selected-image');
}

function parsePayload<T>(stdout: string, predicate: (value: unknown) => value is T, label: string): T {
	const trimmedStdout = stdout.trim();
	if (!trimmedStdout) {
		throw new MrdVizBackendError('The MRD Viz backend returned empty stdout.', stdout, '');
	}

	let payload: unknown;
	try {
		payload = JSON.parse(trimmedStdout);
	} catch (error) {
		const message = error instanceof Error ? error.message : String(error);
		throw new MrdVizBackendError(`The MRD Viz backend returned invalid JSON: ${message}`, stdout, '');
	}

	if (!predicate(payload)) {
		throw new MrdVizBackendError(`The MRD Viz backend returned JSON that does not match the ${label} payload shape.`, stdout, '');
	}

	return payload;
}

export type { MrdImageResponsePayload, MrdOpenPayload };