# Marketplace Release TODO

> **Handoff note (2026-08-14):** Release prep to date was done on the `mrd-viz-release` branch.
> The mechanical/manifest work is complete and validated locally; what remains is (a) creating the
> `ismrmrd` Marketplace publisher + credential, (b) adding the `VSCE_PAT` secret, and (c) the
> compliance sign-off in §5. Once the secret exists, publishing is fully automated on a tag push
> — see [§6 "How the Marketplace publish job works"](#6-how-the-marketplace-publish-job-works)
> for the exact activation steps. Owner sections marked _(Owner: Carter)_ need a new owner.

Tracking checklist for publishing the **MRD Viz** VS Code extension to the VS Code Marketplace
(Channel B). Worked on the `mrd-viz-release` branch.

Context: the repo already ships **Channel A** (GitHub Release of platform VSIXs via
[`mrd_viz_release.yml`](../../.github/workflows/mrd_viz_release.yml)). This checklist covers only
what is still missing to publish to the Marketplace. See the
[Extension Release Runbook](EXTENSION_RELEASE_RUNBOOK.md) for background and the compliance
questions.

Legend: `[ ]` not started · `[~]` in progress · `[x]` done · `[blocked]` waiting on someone else.

---

## 1. Identity & credentials

- [x] **Publisher name** — `ismrmrd` confirmed as the publisher string (already set in
  [`package.json`](../extension/mrd-viz/package.json)). Owner decision resolved: publish under
  the community `ismrmrd` identity.
- [~] **Create the Marketplace publisher** `ismrmrd` at marketplace.visualstudio.com, backed by
  an Azure DevOps org tied to the chosen Microsoft Entra tenant. _(Owner: Carter)_
- [~] **Generate a publish credential** — Azure DevOps PAT (Marketplace → Manage scope) or
  federated/OIDC. _(Owner: Carter)_
- [ ] **Store the credential** as a GitHub Actions secret (`VSCE_PAT`) once the repo/org is
  decided. Confirm approved storage per compliance Q7 for a non-Microsoft-org repo.

## 2. Manifest completeness

- [ ] **Add an `icon`** (128×128 PNG) to the manifest and bundle it in the VSIX.
  - [x] Drop source art at `mrd-viz/extension/mrd-viz/media/icon-src.png`.
  - [x] Resize to exactly 128×128 → `media/icon.png`.
  - [x] Add `"icon": "media/icon.png"` to `package.json`.
- [ ] **Verify README renders standalone** — [`README.md`](../extension/mrd-viz/README.md) becomes
  the Marketplace detail page; ensure any image links are absolute.
- [x] **Confirm LICENSE is included** in the VSIX — copied the repo MIT license to
  `extension/mrd-viz/LICENSE.txt`; confirmed present in the packaged VSIX via `vsce` file list.
- [ ] _(Optional)_ Add `keywords`, refine `categories` (currently `["Other"]`), and a
  `galleryBanner` for discoverability.

## 3. Workflow wiring

- [x] **Add a `publish` job** after `release` in
  [`mrd_viz_release.yml`](../../.github/workflows/mrd_viz_release.yml) that runs
  `vsce publish --packagePath` on each **pre-built** platform VSIX (do not rebuild). One publish
  call per `--target`.
- [x] Guard the job so it is a no-op until the `VSCE_PAT` secret exists (skips with a warning if
  the secret is empty).
- [ ] _(Optional)_ Mirror to **Open VSX** via `ovsx publish` (separate account/token) — TODO left
  in the workflow.
- [ ] **Update PR trigger branch** — the workflow currently filters on `carter-mrd-viz`; point it
  at `main` (or the release branch) once merged.

## 4. Validation loop (local, no publish)

- [x] `vsce package` — validated manifest + produced VSIX without publishing. Confirmed
  `icon.png` and `LICENSE.txt` are included and `icon-src.png` is excluded.
- [x] Install the VSIX locally (`code --install-extension`) — installed as
  `ismrmrd.mrd-viz@0.0.1`; verify listing appearance in the Extensions view.
- [ ] Smoke-test opening a `.mrd` file with a bundled backend binary (local package omits the
  PyInstaller binary; requires a CI build or a local backend build).
- [ ] Only after the above: `vsce publish --packagePath <file>.vsix` (real publish; gated on §1).

## 5. Compliance sign-off (see runbook §5)

- [blocked] Q1–Q3 — employee publishing under non-Microsoft `ismrmrd` publisher; Microsoft
  name/branding usage.
- [blocked] Q4–Q5 — OSS release-approval / registration process.
- [blocked] Q6 — third-party dependency / SBOM / license review for the bundled PyInstaller
  backend.
- [blocked] Q7 — approved credential storage for a non-Microsoft-org repo.
- [blocked] Q8 — code signing / notarization of native backend binaries.

---

## 6. How the Marketplace publish job works

This section documents the `publish-marketplace` job added to
[`mrd_viz_release.yml`](../../.github/workflows/mrd_viz_release.yml) so the next owner can activate
it without reverse-engineering the workflow.

### What it is

It is **a job inside the existing release workflow**, not a separate GitHub Action and not
something that runs on branch pushes. The whole release workflow only does the release/publish
path when a **git tag matching `mrd-viz-v*`** is pushed.

### When it runs

On a `mrd-viz-v*` tag push, the jobs run in this order:

```text
tag mrd-viz-v*  →  build (linux-x64, win32-x64, darwin-arm64 VSIXs)
                 →  release (attaches VSIXs to a GitHub Release)
                 →  publish-marketplace (this job)
```

`publish-marketplace` has `needs: [build, release]` and `if: startsWith(github.ref, 'refs/tags/')`,
so it only runs on a tag and only after the GitHub Release succeeds.

### What it does

- Downloads the **already-built** platform VSIX artifacts (does **not** rebuild — this preserves
  the PyInstaller backend binary that was staged during `build`).
- Runs `npx @vscode/vsce publish --packagePath <vsix>` once per platform VSIX.
- Reads the Marketplace credential from the `VSCE_PAT` environment variable, which is wired to the
  `secrets.VSCE_PAT` GitHub Actions secret.

### Guarded / fail-safe behavior

If the `VSCE_PAT` secret is **not** set, the job prints a warning and exits successfully
(`exit 0`) instead of failing. This means tagging a release today is safe and will simply skip the
Marketplace step until the credential is in place. **No code change is required to activate it —
just add the secret.**

### Steps to activate (for the next owner)

1. Complete §1 (create the `ismrmrd` Marketplace publisher and generate an Azure DevOps PAT with
   the Marketplace → Manage scope) and get compliance sign-off (§5, esp. Q7).
2. In the GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**,
   name it `VSCE_PAT`, paste the PAT value.
3. Bump `version` in [`package.json`](../extension/mrd-viz/package.json) and update the release
   notes in [`README.md`](../extension/mrd-viz/README.md) / `CHANGELOG.md`.
4. Tag and push: `git tag mrd-viz-v0.0.1 && git push origin mrd-viz-v0.0.1`.
5. Watch the Actions run: `build` → `release` → `publish-marketplace`. The extension appears on the
   Marketplace within a few minutes of the publish step succeeding.

### Rollback / safety notes

- A bad publish cannot be deleted, only superseded by a higher version or unpublished by the
  publisher. Prefer a pre-release version (e.g. `0.0.1`) for the first real publish.
- To test the credential without a public publish, run `vsce publish` from a throwaway
  publisher/PAT, or validate the packaging path locally with `vsce package` (see §4).
- Open VSX mirroring is intentionally **not** wired up (a TODO is left in the workflow); it needs a
  separate account and `OVSX_PAT` secret.

---

## Notes / decisions log

- 2026-08-13 — Branch `mrd-viz-release` created for release prep. Publisher owner confirmed as
  `ismrmrd` (community identity, not personal or `microsoft`).
- 2026-08-13 — Added 128×128 `icon.png`, wired into manifest, added `LICENSE.txt`. Local
  `vsce package` + install validated (icon present, source art excluded).
- 2026-08-14 — Scaffolded guarded `publish-marketplace` job in the release workflow (runs on
  `mrd-viz-v*` tag push after `release`; skips if `VSCE_PAT` unset).
