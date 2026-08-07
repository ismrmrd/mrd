import { isMrdImageResponsePayload, isMrdOpenPayload, type MrdImageResponsePayload, type MrdOpenPayload } from './contracts';
import { BACKEND_RESPONSE_MAX_BUFFER_BYTES } from './backendConstants';
import { runProcess } from './subprocess';

export interface BackendRunnerOptions {
	command: string;
	baseArgs: string[];
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

export interface OpenFileResult {
	payload: MrdOpenPayload;
	stderr: string;
}

export async function runOpenFile(filePath: string, options: BackendRunnerOptions, signal?: AbortSignal, explodeSlices = false): Promise<OpenFileResult> {
	const commandArguments = [
		...options.baseArgs,
		'open',
		filePath,
		'--max-thumbnails',
		String(options.maxThumbnails),
		...(explodeSlices ? ['--explode-slices'] : []),
	];
	const result = await execBackend(options.command, commandArguments, options.timeoutMs, signal);
	return { payload: parseOpenPayload(result.stdout, result.stderr), stderr: result.stderr };
}

export interface ImageResult {
	payload: MrdImageResponsePayload;
	stderr: string;
}

export async function runImage(filePath: string, imageIndex: number, options: BackendRunnerOptions, signal?: AbortSignal, sliceCoords?: number[]): Promise<ImageResult> {
	const commandArguments = [
		...options.baseArgs,
		'image',
		filePath,
		'--index',
		String(imageIndex),
		...sliceArgs(sliceCoords),
	];
	const result = await execBackend(options.command, commandArguments, options.timeoutMs, signal);
	return { payload: parseImagePayload(result.stdout, result.stderr), stderr: result.stderr };
}

function sliceArgs(sliceCoords?: number[]): string[] {
	if (!sliceCoords || sliceCoords.length === 0) {
		return [];
	}

	const args: string[] = [];
	sliceCoords.forEach((coord, axis) => {
		if (Number.isInteger(coord) && coord >= 0) {
			args.push('--slice', `${axis}:${coord}`);
		}
	});
	return args;
}

async function execBackend(command: string, commandArguments: string[], timeoutMs: number, signal?: AbortSignal): Promise<{ stdout: string; stderr: string }> {
	const { error, stdout, stderr } = await runProcess(command, commandArguments, {
		timeoutMs,
		maxBuffer: BACKEND_RESPONSE_MAX_BUFFER_BYTES,
		signal,
	});
	if (error && !stdout.trim()) {
		throw new MrdVizBackendError(error.message, stdout, stderr);
	}
	return { stdout, stderr };
}

function parseOpenPayload(stdout: string, stderr: string): MrdOpenPayload {
	return parsePayload(stdout, stderr, isMrdOpenPayload, 'open-file');
}

function parseImagePayload(stdout: string, stderr: string): MrdImageResponsePayload {
	return parsePayload(stdout, stderr, isMrdImageResponsePayload, 'selected-image');
}

function parsePayload<T>(stdout: string, stderr: string, predicate: (value: unknown) => value is T, label: string): T {
	const trimmedStdout = stdout.trim();
	if (!trimmedStdout) {
		throw new MrdVizBackendError('The MRD Viz backend returned empty stdout.', stdout, stderr);
	}

	let payload: unknown;
	try {
		payload = JSON.parse(trimmedStdout);
	} catch (error) {
		const message = error instanceof Error ? error.message : String(error);
		throw new MrdVizBackendError(`The MRD Viz backend returned invalid JSON: ${message}`, stdout, stderr);
	}

	if (!predicate(payload)) {
		throw new MrdVizBackendError(`The MRD Viz backend returned JSON that does not match the ${label} payload shape.`, stdout, stderr);
	}

	return payload;
}

export type { MrdImageResponsePayload, MrdOpenPayload };