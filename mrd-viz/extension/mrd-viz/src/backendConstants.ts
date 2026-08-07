// Centralized timeouts, buffer sizes, and backend invocation constants so the several subprocess
// call sites (resolver probe, backend run, Python-version probe, provisioning) don't drift.

/** Default per-process backend timeout. Must match the `mrdViz.backendTimeoutMs` default in package.json. */
export const BACKEND_TIMEOUT_MS_DEFAULT = 30_000;

/** Bounds applied to the configured timeout when probing a candidate with `--version`. */
export const PROBE_TIMEOUT_MS_MIN = 1_000;
export const PROBE_TIMEOUT_MS_MAX = 15_000;

/** Timeout for the quick `sys.version_info` probe used to find a provisioning interpreter. */
export const PYTHON_VERSION_PROBE_TIMEOUT_MS = 10_000;

/** Timeout for one provisioning step (venv creation / pip install); pip installs can be slow. */
export const PROVISIONING_STEP_TIMEOUT_MS = 10 * 60 * 1_000;

/** stdout/stderr buffer for a backend payload response (base64 PNGs can be large). */
export const BACKEND_RESPONSE_MAX_BUFFER_BYTES = 64 * 1024 * 1024;

/** stdout/stderr buffer for a provisioning step's logs. */
export const PROVISIONING_LOG_MAX_BUFFER_BYTES = 10 * 1024 * 1024;

/** Leading args that invoke the backend CLI through a Python interpreter. */
export const PYTHON_MODULE_ARGS = ['-m', 'mrd_viz.cli'] as const;

/** The pip distribution name for the backend (not yet published to PyPI). */
export const PYPI_PACKAGE_NAME = 'mrd-viz';

/** Interpreter commands tried, in order, when discovering a Python to build the managed venv. */
export const PROVISIONING_PYTHON_CANDIDATES = ['python3.12', 'python3', 'python'] as const;
