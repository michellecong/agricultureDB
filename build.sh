#!/bin/bash
set -e
pip install --no-cache-dir -r requirements.txt
cd frontend
npm ci --legacy-peer-deps
CI=false GENERATE_SOURCEMAP=false REACT_APP_API_URL=/api npm run build
