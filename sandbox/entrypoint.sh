#!/bin/bash
# Archie sandbox entrypoint — bootstrap and hand off to archie.

export ARCHIE_SANDBOX=1

# Install archie CLI from mounted repo (editable install for live code)
uv tool install -e /opt/archie --quiet

exec archie kiro "$@"
