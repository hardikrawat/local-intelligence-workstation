#!/bin/bash
cd "$(dirname "$0")"

PORT=3300
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; do
    PORT=$((PORT+1))
done

echo "Starting Ollama Studio on http://localhost:$PORT ..."
python3 -m http.server $PORT &
SERVER_PID=$!

sleep 0.8
open "http://localhost:$PORT"

trap "kill $SERVER_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT
wait $SERVER_PID
