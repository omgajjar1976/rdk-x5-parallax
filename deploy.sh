#!/usr/bin/env bash
# Copy the committed tree (no .git) to the board and record the revisions there.
set -euo pipefail
cd "$(dirname "$0")"
[ -z "$(git status --porcelain)" ] || { echo "uncommitted changes: commit first"; exit 1; }
HOST=${1:-rdk}
tmp=$(mktemp -d); git archive HEAD | tar -x -C "$tmp"
git log --format='%h %s' > "$tmp/.revisions"
rsync -a --delete "$tmp/" "$HOST:~/stage1/"
rm -rf "$tmp"; echo "deployed $(git log -1 --format=%h) to $HOST:~/stage1"
