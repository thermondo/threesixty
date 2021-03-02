#!/usr/bin/env bash

# Add a little Heroku style syntax sugar.

indent() {
  sed "s/^/       /"
}

puts-step() {
  echo "-----> $*"
}
