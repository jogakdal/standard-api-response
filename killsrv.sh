#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <port>"
  exit 1
fi

PORT=$1

PID=$(lsof -t -i :$PORT)

if [ -n "$PID" ]; then
  kill -9 $PID
  echo "Process on port $PORT (PID: $PID) has been killed."
else
  echo "No process found running on port $PORT."
fi
