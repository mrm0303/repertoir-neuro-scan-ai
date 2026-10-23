#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
if [ -f ".venv/bin/python3" ]; then
    exec ".venv/bin/python3" catalogue_disques_v3.py "$@"
else
    exec python3 catalogue_disques_v3.py "$@"
fi
