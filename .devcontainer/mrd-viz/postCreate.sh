#!/usr/bin/env bash
# postCreate for the MRD Viz dev container.
# Installs the generic CLI tools the workflow needs. Project provisioning
# (backend + extension) is a one-time `just container-setup` run by the user.
set -euo pipefail

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

cat <<'EOF'

============================================================
 MRD Viz dev container is ready.

 Next step (run once):
     just mrd-viz-container-setup

 That creates the backend virtualenv, installs mrd_viz, and
 builds + installs the MRD Viz extension in this window.
============================================================
EOF
