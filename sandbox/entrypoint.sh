#!/bin/bash
# Set terminal title if provided, suppressing any Docker/shell default
if [ -n "$ARCHIE_TITLE" ]; then
    printf '\033]0;%s\007' "$ARCHIE_TITLE"
fi
exec "$@"
