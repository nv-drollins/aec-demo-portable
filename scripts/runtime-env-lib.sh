#!/usr/bin/env bash
# Load config/runtime.env into the environment for shell launchers.
#
# portable_stack.py already reads runtime.env, but the Hermes launchers did
# not, so editing AEC_HERMES_MODEL in runtime.env changed the preflight check
# while the launcher silently kept its own hardcoded default. Source this file
# to make runtime.env the single source of truth for both.
#
# Existing environment variables win, so a one-off
# `AEC_HERMES_MODEL=... ./scripts/start-portable-manual-demo.sh` still works.

aec_load_runtime_env() {
    local root=$1
    local file="$root/config/runtime.env"
    [[ -f "$file" ]] || file="$root/config/runtime.env.example"
    [[ -f "$file" ]] || return 0

    export AEC_PORTABLE_ROOT="$root"
    local line key value
    while IFS= read -r line; do
        line="${line#"${line%%[![:space:]]*}"}"
        [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue
        key="${line%%=*}"
        value="${line#*=}"
        key="${key//[[:space:]]/}"
        [[ -z "$key" ]] && continue
        # Only set what the caller has not already provided.
        [[ -n "${!key:-}" ]] && continue
        # runtime.env values reference $AEC_PORTABLE_ROOT and ~; expand both.
        value="$(eval printf '%s' "\"$value\"" 2>/dev/null)" || continue
        export "$key=$value"
    done < "$file"
}
