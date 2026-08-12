#!/usr/bin/env bash
# postCreate for the MRD Viz dev container.
# Installs the generic CLI tools the workflow needs, then best-effort provisions
# the backend virtualenv so the container is turnkey for a first run. Building and
# installing the extension VSIX stays a one-time `just mrd-viz-container-setup`
# step (it needs the npm registry, which is what fails on restricted networks).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Resolve the container architecture so the Node and azcopy downloads match it.
arch="$(uname -m)"
case "$arch" in
	x86_64)        node_arch="x64";   azcopy_url="https://aka.ms/downloadazcopy-v10-linux";       azcopy_glob="azcopy_linux_amd64_*" ;;
	aarch64|arm64) node_arch="arm64"; azcopy_url="https://aka.ms/downloadazcopy-v10-linux-arm64"; azcopy_glob="azcopy_linux_arm64_*" ;;
	*) echo ">> Unsupported architecture: $arch" >&2; exit 1 ;;
esac

# Node.js (from nodejs.org, which is reachable even where the public npm registry
# is blocked). Installed here instead of the devcontainer `node` feature, which
# pulls pnpm from the public npm registry at build time. Node bundles npm.
if ! command -v node >/dev/null 2>&1; then
	echo ">> Installing Node.js"
	node_version="v24.18.0"
	curl -fsSL "https://nodejs.org/dist/${node_version}/node-${node_version}-linux-${node_arch}.tar.xz" -o /tmp/node.tar.xz
	sudo tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1
	rm -f /tmp/node.tar.xz
fi

# just: task runner used by `just container-setup`.
if ! command -v just >/dev/null 2>&1; then
	echo ">> Installing just"
	curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh -o /tmp/just-install.sh
	sudo bash /tmp/just-install.sh --to /usr/local/bin
	rm -f /tmp/just-install.sh
fi

# azcopy: used to pull .mrd data from Azure storage.
if ! command -v azcopy >/dev/null 2>&1; then
	echo ">> Installing azcopy"
	curl -sSL "$azcopy_url" -o /tmp/azcopy.tar.gz
	tar -xzf /tmp/azcopy.tar.gz -C /tmp
	sudo cp /tmp/${azcopy_glob}/azcopy /usr/local/bin/azcopy
	sudo chmod +x /usr/local/bin/azcopy
	rm -rf /tmp/azcopy.tar.gz /tmp/${azcopy_glob}
fi

# Backend provisioning (best-effort, non-fatal). The dev container points
# mrdViz.backendPath at this venv, so create it and install the mrd_viz backend
# now for a turnkey first run. This only needs PyPI (mrd-python/numpy/pillow),
# which is typically reachable even where the npm registry is blocked; the guard
# keeps a failure from aborting container creation and falls back to the manual
# step in the banner below.
venv="$HOME/.venvs/mrd-viz"
backend_dir="$repo_root/mrd-viz/backend"
backend_ready=0
if [ -x "$venv/bin/python" ] && "$venv/bin/python" -m mrd_viz.cli --version >/dev/null 2>&1; then
	backend_ready=1
elif [ -d "$backend_dir" ]; then
	# Point pip at the first reachable index (internal mirror, else public PyPI).
	# shellcheck source=./select-pkg-index.sh
	source "$repo_root/.devcontainer/mrd-viz/select-pkg-index.sh"
	echo ">> Provisioning MRD Viz backend virtualenv: $venv"
	if python3 -m venv "$venv" \
		&& "$venv/bin/python" -m pip install --upgrade pip \
		&& "$venv/bin/python" -m pip install -e "$backend_dir"; then
		backend_ready=1
	else
		echo ">> WARNING: automatic backend setup failed (often a blocked/restricted network)." >&2
		rm -rf "$venv"
	fi
fi

if [ "$backend_ready" -eq 1 ]; then
	cat <<'EOF'

============================================================
 MRD Viz dev container is ready. Backend is installed and
 mrdViz.backendPath points at ~/.venvs/mrd-viz, so opening a
 .mrd file should work out of the box.

 If the MRD Viz extension itself is not installed yet, run:
     just mrd-viz-container-setup
 (builds + installs the extension VSIX; needs npm registry
  access - see mrd-viz/docs/DEVCONTAINER.md for restricted
  networks).
============================================================
EOF
else
	cat <<'EOF'

============================================================
 MRD Viz dev container is ready, but automatic backend setup
 did not complete (often a blocked/restricted network).

 Finish setup by running:
     just mrd-viz-container-setup

 That creates the backend virtualenv, installs mrd_viz, and
 builds + installs the MRD Viz extension in this window.
 See mrd-viz/docs/DEVCONTAINER.md for restricted-network tips.
============================================================
EOF
fi
