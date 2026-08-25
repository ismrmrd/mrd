# D3 Bundled Backend Verification

D3 packages the Python backend as a PyInstaller one-dir bundle inside each platform VSIX. The implementation exists; this scaffold defines the artifact contract that release automation and onboarding can rely on.

## Artifact contract

Each staged `extension/mrd-viz/media/backend/` directory must contain:

- `mrd-viz` (`mrd-viz.exe` on Windows);
- a non-empty `_internal/` PyInstaller runtime;
- an executable that returns `mrd-viz <version>` for `--version`;
- `backend-manifest.json`, generated from the verified artifact with target, version, size, and SHA-256.

Verify a staged bundle from `mrd-viz/`:

```bash
just verify-bundled-backend linux-x64
```

Run the release-tool contract tests:

```bash
just test-release-tools
```

## Next wiring

The release matrix should invoke the verifier after staging and before `vsce package`. Because the manifest is written into `media/backend/`, it is included in the VSIX and can later support diagnostics, provenance display, and researcher bug reports without probing platform-specific file metadata.
