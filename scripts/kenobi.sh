#!/usr/bin/env bash
# Act on GitHub as knowb-kenobi[bot] for this repository.
#
# Every agent commit, push, and pull request in this repository goes through
# this script. It wraps knowledgeHQ's sanctioned mcp/scripts/as-kenobi.sh, which
# mints a short-lived, repository-scoped installation token for the knowb-ai
# GitHub App from the macOS Keychain and never prints it.
#
# The person invoking the request is resolved from their own `gh` login and
# becomes the pull request reviewer and assignee, and the human Co-Authored-By
# trailer on commits:
#
#   scripts/kenobi.sh git commit -m "..."
#   scripts/kenobi.sh git push -u origin my-branch
#   scripts/kenobi.sh gh pr create --title "..." --body-file -
#
# Set KNOWB_HQ when knowledgeHQ is not checked out next to this repository.
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "usage: $0 <git|gh> [args...]" >&2
  exit 2
fi

# The bot opens pull requests; the invoking reviewer merges them.
if [ "${1:-}" = gh ] && [ "${2:-}" = pr ] && [ "${3:-}" = merge ]; then
  echo "kenobi: knowb-kenobi[bot] never merges; the reviewer merges" >&2
  exit 2
fi

here=$(cd "$(dirname "$0")" && pwd)
hq="${KNOWB_HQ:-$here/../../knowledgeHQ}"
as_kenobi="$hq/mcp/scripts/as-kenobi.sh"
if [ ! -x "$as_kenobi" ]; then
  echo "kenobi: $as_kenobi not found; set KNOWB_HQ to your knowledgeHQ checkout" >&2
  exit 2
fi

# The invoking account comes from the caller's own gh login, never a bot token.
if [ -z "${KENOBI_OWNER_LOGIN:-}" ]; then
  read -r login id < <(env -u GH_TOKEN -u GITHUB_TOKEN gh api user --jq '"\(.login) \(.id)"')
  if [ -z "${login:-}" ] || [ -z "${id:-}" ]; then
    echo "kenobi: could not resolve the invoking GitHub account; run gh auth login" >&2
    exit 2
  fi
  export KENOBI_OWNER_LOGIN="$login"
  export KENOBI_OWNER_COAUTHOR="$login <$id+$login@users.noreply.github.com>"
fi

exec "$as_kenobi" "$@"
