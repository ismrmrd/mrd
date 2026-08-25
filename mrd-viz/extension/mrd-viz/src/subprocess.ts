import { execFile, type ExecFileException } from 'node:child_process';

/** Options for {@link runProcess}. Each caller sets the timeout/buffer that suits its workload. */
export interface RunProcessOptions {
	timeoutMs: number;
	/** Max stdout/stderr bytes; omit to use Node's default. */
	maxBuffer?: number;
	/** Abort signal to cancel an in-flight process. */
	signal?: AbortSignal;
}

/** Result of a finished process: its captured output plus any spawn/exit error. */
export interface ProcessOutcome {
	error?: ExecFileException;
	stdout: string;
	stderr: string;
}

/**
 * Thin wrapper over `execFile` for short-lived subprocesses: it standardizes the option plumbing
 * (timeout, buffer, `windowsHide`, abort signal) and resolves with `{ error, stdout, stderr }` so
 * each caller keeps its own error shaping rather than sharing one policy.
 */
export function runProcess(command: string, args: string[], options: RunProcessOptions): Promise<ProcessOutcome> {
	return new Promise(resolve => {
		execFile(
			command,
			args,
			{ timeout: options.timeoutMs, maxBuffer: options.maxBuffer, windowsHide: true, signal: options.signal },
			(error, stdout, stderr) => {
				resolve({ error: error ?? undefined, stdout: stdout.toString(), stderr: stderr.toString() });
			},
		);
	});
}
