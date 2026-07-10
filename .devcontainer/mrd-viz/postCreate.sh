#!/usr/bin/env bash
# postCreate for the MRD Viz dev container.
# Installs the generic CLI tools the workflow needs. Project provisioning
# (backend + extension) is a one-time `just container-setup` run by the user.
set -euo pipefail

# Node.js (from nodejs.org, which is reachable even where the public npm registry
# is blocked). Installed here instead of the devcontainer `node` feature, which
# pulls pnpm from the public npm registry at build time. Node bundles npm.
if ! command -v node >/dev/null 2>&1; then
	echo ">> Installing Node.js"
	node_version="v24.18.0"
	curl -fsSL "https://nodejs.org/dist/${node_version}/node-${node_version}-linux-x64.tar.xz" -o /tmp/node.tar.xz
	sudo tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1
	rm -f /tmp/node.tar.xz
fi

# just: task runner used by `just container-setup`.
if ! command -v just >/dev/null 2>&1; then
	echo ">> Installing just"
	curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | sudo bash -s -- --to /usr/local/bin
fi

# azcopy: used to pull .mrd data from Azure storage.
if ! command -v azcopy >/dev/null 2>&1; then
	echo ">> Installing azcopy"
	curl -sSL https://aka.ms/downloadazcopy-v10-linux -o /tmp/azcopy.tar.gz
	tar -xzf /tmp/azcopy.tar.gz -C /tmp
	sudo cp /tmp/azcopy_linux_amd64_*/azcopy /usr/local/bin/azcopy
	sudo chmod +x /usr/local/bin/azcopy
	rm -rf /tmp/azcopy.tar.gz /tmp/azcopy_linux_amd64_*
fi

cat <<'EOF'

============================================================
 MRD Viz dev container is ready.

 Next step (run once):
     cd mrd-viz && just container-setup

 That creates the backend virtualenv, installs mrd_viz, and
 builds + installs the MRD Viz extension in this window.
============================================================
EOF
