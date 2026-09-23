#!/bin/sh
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
git -C "$repo_dir" pull --ff-only
exec sh "$repo_dir/install.sh" "$@"
