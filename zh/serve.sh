#!/bin/bash
echo "Starting Word-Lerning local server..."
echo "Open http://localhost:8080/tools/word-triage/ in your browser."
echo "Press Ctrl+C to stop."
cd "$(dirname "$0")"
python3 -m http.server 8080
