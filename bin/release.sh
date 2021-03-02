#!/usr/bin/env bash

# Command that gets called after each Heroku release.

set -eo pipefail


BIN_DIR=$(cd "$(dirname "$0")"; pwd)
PYTHON=$(which python3)
DISABLE_CHECKS=${DISABLE_CHECKS:-"0"}
DISABLE_MIGRATIONS=${DISABLE_MIGRATIONS:-"0"}

# shellcheck source=bin/utils.sh
source "$BIN_DIR/utils.sh"

if [ "$DISABLE_CHECKS" -eq "0" ]; then
  puts-step "Running deployment checks"
  ${PYTHON} manage.py check --deploy | indent
fi

if [ "$DISABLE_MIGRATIONS" -eq "0" ]; then
  puts-step "Running migrations"
  ${PYTHON} manage.py migrate --no-input | indent
fi

puts-step "Done!"
