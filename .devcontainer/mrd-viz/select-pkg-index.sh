# shellcheck shell=bash
# Pick the first reachable package index/registry from an ordered, space-separated
# candidate list and export the variables pip and npm read natively
# (PIP_INDEX_URL, npm_config_registry). Source this before running pip/npm.
#
# Candidate ladder (same idea as the backend resolver): the Microsoft-internal
# mirror is tried first, the public registry second. Microsoft-internal devs on a
# restricted network get the mirror; external devs fall back to the public
# registry automatically. The lists come from devcontainer.json (remoteEnv):
#   MRD_PIP_INDEX_URLS   e.g. "https://internal/pypi/simple/ https://pypi.org/simple/"
#   MRD_NPM_REGISTRIES   e.g. "https://internal/npm/ https://registry.npmjs.org/"
# When unset (running outside the dev container), they default to public only.
#
# Override the final choice by exporting PIP_INDEX_URL / npm_config_registry
# yourself before sourcing; an explicit value is always respected.

: "${MRD_PIP_INDEX_URLS:=https://pypi.org/simple/}"
: "${MRD_NPM_REGISTRIES:=https://registry.npmjs.org/}"

# Echo the first URL in $1 (space-separated) whose host completes an HTTPS request
# within a short timeout. Any HTTP response (even 404) counts as reachable; only a
# TLS handshake / connection failure — the restricted-network symptom — is a miss.
_mrd_first_reachable() {
	local url
	for url in $1; do
		if curl -sS --max-time 6 -o /dev/null -I "$url" >/dev/null 2>&1; then
			printf '%s' "$url"
			return 0
		fi
	done
	return 1
}

# pip
if [ -n "${PIP_INDEX_URL:-}" ]; then
	echo ">> Using PyPI index (from PIP_INDEX_URL): $PIP_INDEX_URL"
elif _pip_url="$(_mrd_first_reachable "$MRD_PIP_INDEX_URLS")"; then
	export PIP_INDEX_URL="$_pip_url"
	echo ">> Using PyPI index: $PIP_INDEX_URL"
else
	echo ">> WARNING: no reachable PyPI index among: $MRD_PIP_INDEX_URLS" >&2
	echo ">> If you are on a restricted/corporate network, run this and retry:" >&2
	echo ">>     export PIP_INDEX_URL=\"${MRD_PIP_INDEX_URLS%% *}\"" >&2
fi

# npm
if [ -n "${npm_config_registry:-}" ]; then
	echo ">> Using npm registry (from npm_config_registry): $npm_config_registry"
elif _npm_url="$(_mrd_first_reachable "$MRD_NPM_REGISTRIES")"; then
	export npm_config_registry="$_npm_url"
	echo ">> Using npm registry: $npm_config_registry"
else
	echo ">> WARNING: no reachable npm registry among: $MRD_NPM_REGISTRIES" >&2
	echo ">> If you are on a restricted/corporate network, run this and retry:" >&2
	echo ">>     export npm_config_registry=\"${MRD_NPM_REGISTRIES%% *}\"" >&2
fi

unset -f _mrd_first_reachable
unset _pip_url _npm_url
