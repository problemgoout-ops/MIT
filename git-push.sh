#!/bin/bash
# Push to GitHub
cd "$(dirname "$0")"
git add index.html
git commit -m "Update assistent landing page" || true
git push origin main
echo "Pushed to https://github.com/problemgoout-ops/MIT"
