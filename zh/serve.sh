#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Word-Lerning local server..."
echo ""
echo "  Web tool: http://localhost:8080/tools/word-triage/"
echo ""
echo "Press Ctrl+C to stop."
echo ""

# Open browser (detect OS)
if command -v open &>/dev/null; then
    open "http://localhost:8080/tools/word-triage/" &
elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:8080/tools/word-triage/" &
elif command -v start &>/dev/null; then
    start "http://localhost:8080/tools/word-triage/" &
fi

python3 -m http.server 8080
