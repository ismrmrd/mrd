import { execFile } from 'node:child_process';

import { isMrdOpenPayload, type MrdOpenPayload } from './contracts';

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
				if (error) {
					reject(new MrdVizBackendError(error.message, stdoutText, stderrText));
					return;
				}

				resolve({ stdout: stdoutText, stderr: stderrText });
			},
		);
	});
}

function parseOpenPayload(stdout: string): MrdOpenPayload {
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

	if (!isMrdOpenPayload(payload)) {
		throw new MrdVizBackendError('The MRD Viz backend returned JSON that does not match the open-file payload shape.', stdout, '');
	}

	return payload;
}

export type { MrdOpenPayload };