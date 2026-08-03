# Extension Release Runbook

This document defines what is required to release the MRD Viz VS Code extension, the concrete
release steps, the publisher-identity decision, and the compliance questions to raise with the
Monarch team before publishing to the VS Code Marketplace.

Related runbooks:

- [Official Extension Development Runbook](OFFICIAL_EXT_DEV_RUNBOOK.md) — backend + dev host setup.
- [Packaging & Local Install Runbook](PACKAGING_AND_INSTALL_RUNBOOK.md) — build/install a VSIX locally.

## 1. What "release" means — two distinct channels

The repo currently supports **only channel A**. Channel B (Marketplace) is scaffolded
(`publisher: ismrmrd` is set in the manifest) but is **not** wired up.

| | A. GitHub Release (VSIX artifact) | B. VS Code Marketplace publish |
|---|---|---|
| Status in repo | ✅ Implemented — [`.github/workflows/mrd_viz_release.yml`](../../.github/workflows/mrd_viz_release.yml) | ❌ Not implemented (`vsce publish` absent) |
| How users install | Download `.vsix`, `code --install-extension` | One-click "Install" in VS Code |
| Accounts needed | GitHub write access only | Marketplace publisher + Entra tenant + PAT/federated creds |
| Review/approval | None (self-service) | Marketplace automated scan; "verified publisher" is extra |
| Trigger | push tag `mrd-viz-v*` | would be a new job in the workflow |

## 2. Accounts, credentials & review needed

### Channel A — GitHub Release (already working)

- GitHub repo write/tag permission. That is all.
- The tag `mrd-viz-v*` triggers a matrix build (`linux-x64`, `win32-x64`, `darwin-arm64`),
  bundles the PyInstaller backend binary into each VSIX, and the `release` job
  attaches the VSIXs to a GitHub Release. No external accounts.

### Channel B — VS Code Marketplace (needs decisions)

- **A Marketplace publisher** — the `publisher` string in
  [`package.json`](../extension/mrd-viz/package.json) (currently `ismrmrd`). A publisher is
  created at marketplace.visualstudio.com and is backed by an **Azure DevOps org tied to a
  Microsoft Entra (AAD) tenant**.
- **A Personal Access Token** (Azure DevOps, Marketplace → Manage scope) or Azure
  **federated/OIDC credentials** for CI. This secret must live somewhere (GitHub Actions
  secret) — a compliance touchpoint.
- **Marketplace validation** — automated malware/manifest scan on every publish. Usually
  seconds; no human review for a normal publisher.
- **Verified-publisher badge** (optional) — requires domain verification (e.g. proving control
  of an ismrmrd domain).
- **Open VSX** (optional) — publish here for VSCodium / Cursor / code-server users; separate
  account and token.

## 3. Release steps, concretely

### Today — GitHub Release (no new decisions)

1. Bump `version` in [`package.json`](../extension/mrd-viz/package.json) and update the Release
   Notes in [`README.md`](../extension/mrd-viz/README.md).
2. `git tag mrd-viz-v0.0.1 && git push origin mrd-viz-v0.0.1`.
3. The workflow builds the 3 platform VSIXs and publishes the GitHub Release.
4. Users install via the [Packaging & Local Install Runbook](PACKAGING_AND_INSTALL_RUNBOOK.md).

Notes / caveats:

- The workflow's `on.pull_request.branches` filter is `carter-mrd-viz`.
- `darwin-x64` (Intel macOS, `macos-13`) was **dropped** from the matrix: GitHub is winding
  down the Intel macOS runner pool, so the job sat in the queue for hours without ever being
  assigned a runner (0 steps, cancelled at GitHub's ~24h queue limit; `timeout-minutes` does
  not help because it only counts execution time, not queue time). We do not currently ship to
  Intel Macs; those users can still use the extension via the managed-venv / "Select Python
  Interpreter" fallback. Re-add the leg (or use a paid `macos-13-large` / self-hosted Intel
  runner) if Intel-Mac bundled-binary support is needed.

### Later — add Marketplace publishing

1. Decide/claim the publisher identity (section 4).
2. Store the PAT as a GH Actions secret (`VSCE_PAT`) or set up OIDC.
3. Add a job after `release`:
   `npx --yes @vscode/vsce publish --packagePath dist/**/*.vsix` — publish the pre-built platform
   VSIXs; do **not** rebuild.
4. Optionally mirror to Open VSX with `ovsx publish`.

## 4. Which publisher name?

**Recommendation: `ismrmrd`** (which the manifest already assumes), **not** a personal name and
**not** `microsoft`.

- **Personal name** — ❌ ties a community/standards-body tool to one individual; ownership is
  lost when that person rolls off. Only acceptable as a throwaway for testing.
- **`ismrmrd`** — ✅ matches the repo, the standard, and the existing `publisher` field. It is
  the natural community-owned identity. Open question: *which* Entra tenant/account owns the
  `ismrmrd` publisher, and who holds the credentials long-term (the ISMRMRD org, not an
  individual).
- **`microsoft`** — ❌ the official Microsoft publisher is a tightly controlled, verified
  publisher governed by Microsoft's internal release process. Using it implies Microsoft *owns*
  this ISMRMRD project and forces the full official-extension pipeline. Almost certainly not the
  intent for a community MR data format viewer.
- **A new Microsoft-adjacent publisher** (e.g. a lab/team publisher) — only if Microsoft wants to
  formally own/brand it. This is a Monarch question.

The real question is not cosmetic — it is *who is the legal/organizational owner of the published
artifact*, and that is what compliance decides.

## 5. Questions for the Monarch compliance expert

### Ownership & identity

1. This is an open-source project under the **ISMRMRD** org (not a Microsoft product), but the
   work is being done by a Microsoft employee. Can/should it be published to the VS Code
   Marketplace under a **non-Microsoft `ismrmrd` publisher**, or must anything published by an
   employee go under a Microsoft-governed publisher?
2. If it goes out under `ismrmrd`, is there any restriction on a Microsoft employee owning/
   operating that publisher account and its Entra tenant?
3. Are we allowed to use the **Microsoft name/logo/branding** anywhere (publisher, README, icon),
   or must we avoid implying Microsoft ownership/endorsement?

### Process & approvals

4. Does publishing a VS Code extension (even community-owned) require going through **Microsoft's
   official extension release / OSS release process**, or is a GitHub Release of a VSIX outside
   that scope?
5. Is there an OSS **release-approval / registration** step (e.g. through the Microsoft open
   source program) required before tagging a public release?
6. Do the **bundled third-party dependencies** (the PyInstaller-packaged Python backend + its
   transitive deps, and the npm deps) need a license/SBOM/attribution review before distribution?

### Security & secrets

7. What is the approved way to store the **Marketplace publish credential** (Azure DevOps PAT vs.
   federated OIDC) for a repo that is not in a Microsoft-owned org?
8. Do we need **code signing / notarization** of the bundled native backend binaries (Windows
   Authenticode / macOS notarization) for compliance, beyond removing SmartScreen/Gatekeeper
   prompts? (There is already a TODO for this in the workflow.)

### Data & telemetry

9. The extension ships no telemetry today — if we later add any, what compliance/privacy
   requirements apply?
10. Any **export-control / distribution** constraints on shipping the compiled backend binaries in
    the Marketplace VSIXs?
