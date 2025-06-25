#!/bin/bash

# Start Django server in background with proper detachment

echo "Starting Django server in background..."

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Kill any existing Django processes on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Create logs directory if it doesn't exist
mkdir -p logs

# Start server with nohup, completely detached from terminal
nohup python manage.py runserver 0.0.0.0:8000 --noreload > logs/django_server.log 2>&1 &

# Save PID
echo $! > server.pid

echo "✓ Django server started successfully!"
echo "  - Server PID: $(cat server.pid)"
echo "  - Running at: http://localhost:8000"
echo "  - Log file: logs/django_server.log"
echo ""
echo "To monitor logs: tail -f logs/django_server.log"
echo "To stop server: kill $(cat server.pid)"