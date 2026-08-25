# MRD Viz Release

GitHub Releases are the first researcher distribution channel. Each release provides platform VSIXs containing the extension and standalone backend.

## Publish

1. Update `version` in `extension/mrd-viz/package.json` and `package-lock.json`.
2. Move the relevant extension changelog entries out of `Unreleased`.
3. Merge after the MRD Viz and MRD Viz Release checks pass.
4. Create and push an annotated tag matching the manifest exactly:

   ```bash
   git tag -a mrd-viz-v0.0.1 -m "MRD Viz 0.0.1"
   git push origin mrd-viz-v0.0.1
   ```

The release workflow rejects a mismatched tag, builds and smoke-tests the standalone backend on each supported platform, packages targeted VSIXs, and attaches them to a generated GitHub Release. A manual workflow run produces the same downloadable artifacts without publishing a release.

## Researcher install

1. Open <https://github.com/ismrmrd/mrd/releases/latest>.
2. Download the VSIX matching the researcher's platform.
3. In VS Code, run **Extensions: Install from VSIX...**.
4. Open a `.mrd` file.

Linux x64, Windows x64, and Apple Silicon builds include the backend. Intel macOS and other unsupported platforms use **MRD Viz: Set Up Backend** or **MRD Viz: Select Python Interpreter**; the automatic fallback requires Python 3.12 and a published `mrd-viz` package source.
