#!/bin/bash
# Start local web server for Ollama Studio
cd "$(dirname "$0")"

PORT=3300
# Find an available port if 3300 is busy
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; do
    PORT=$((PORT+1))
done

echo "Starting Ollama Studio on http://localhost:$PORT/chat.html ..."
python3 server.py $PORT &
SERVER_PID=$!

sleep 0.8
open "http://localhost:$PORT/chat.html"

# Trap Ctrl+C or terminal exit to terminate background server
trap "kill $SERVER_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT
wait $SERVER_PID
