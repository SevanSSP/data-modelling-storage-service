#!/usr/bin/env sh
set -euo pipefail

echo "ENVIRONMENT: $ENVIRONMENT"
export FLASK_APP="/code/app.py"

flask nuke-db

if [ "$ENVIRONMENT" = 'local' ]; then
    flask drop-data-sources
    echo "Importing DataSources"
    for dataSource in /code/home/data_sources/"local"*.json ; do
      flask import-data-source "$dataSource"
    done
fi

flask init-application
