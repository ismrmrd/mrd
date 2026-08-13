# Marketplace Release TODO

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
- [ ] **Confirm LICENSE is included** in the VSIX (check
  [`.vscodeignore`](../extension/mrd-viz/.vscodeignore); `license: MIT` is declared).
- [ ] _(Optional)_ Add `keywords`, refine `categories` (currently `["Other"]`), and a
  `galleryBanner` for discoverability.

## 3. Workflow wiring

- [ ] **Add a `publish` job** after `release` in
  [`mrd_viz_release.yml`](../../.github/workflows/mrd_viz_release.yml) that runs
  `vsce publish --packagePath` on each **pre-built** platform VSIX (do not rebuild). One publish
  call per `--target`.
- [ ] Guard the job so it is a no-op until the `VSCE_PAT` secret exists.
- [ ] _(Optional)_ Mirror to **Open VSX** via `ovsx publish` (separate account/token).
- [ ] **Update PR trigger branch** — the workflow currently filters on `carter-mrd-viz`; point it
  at `main` (or the release branch) once merged.

## 4. Validation loop (local, no publish)

- [ ] `vsce package --target win32-x64` — validate manifest + produce VSIX without publishing.
- [ ] `vsce ls` — confirm icon, LICENSE, README, and staged backend binary are included and
  `node_modules` is excluded.
- [ ] Install the VSIX locally (`code --install-extension`) and smoke-test opening a `.mrd` file.
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

## Notes / decisions log

- 2026-08-13 — Branch `mrd-viz-release` created for release prep. Publisher owner confirmed as
  `ismrmrd` (community identity, not personal or `microsoft`).
