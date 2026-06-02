#!/bin/bash
# Archie sandbox entrypoint — setup and passthrough.

# Install archie CLI from mounted repo (editable install for live code)
uv tool install -e /opt/archie --quiet

exec "$@"
