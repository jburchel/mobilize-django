#!/bin/bash

# Celery startup script for Mobilize CRM
# This script helps start Celery worker and beat scheduler

echo "Mobilize CRM - Celery Startup Script"
echo "===================================="

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   brew services start redis"
    echo "   or"
    echo "   redis-server"
    exit 1
fi

echo "✅ Redis is running"

# Function to start Celery worker
start_worker() {
    echo "Starting Celery Worker..."
    celery -A mobilize worker --loglevel=info --concurrency=4
}

# Function to start Celery beat
start_beat() {
    echo "Starting Celery Beat (scheduler)..."
    celery -A mobilize beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
}

# Function to start flower monitoring
start_flower() {
    echo "Starting Flower (Celery monitoring)..."
    celery -A mobilize flower --port=5555
}

# Function to show help
show_help() {
    echo "Usage: $0 [worker|beat|flower|all|help]"
    echo ""
    echo "Commands:"
    echo "  worker  - Start Celery worker"
    echo "  beat    - Start Celery beat scheduler" 
    echo "  flower  - Start Flower monitoring interface"
    echo "  all     - Start all components (requires multiple terminals)"
    echo "  help    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 worker          # Start worker only"
    echo "  $0 beat            # Start beat scheduler only"
    echo "  $0 all             # Show commands to run in separate terminals"
}

# Parse command line argument
case "${1:-help}" in
    worker)
        start_worker
        ;;
    beat)
        start_beat
        ;;
    flower)
        start_flower
        ;;
    all)
        echo "To start all Celery components, run these commands in separate terminals:"
        echo ""
        echo "Terminal 1 (Worker):"
        echo "  $0 worker"
        echo ""
        echo "Terminal 2 (Beat Scheduler):"
        echo "  $0 beat"
        echo ""
        echo "Terminal 3 (Flower - Optional):"
        echo "  $0 flower"
        echo ""
        echo "Then visit http://localhost:5555 for Celery monitoring"
        ;;
    help|*)
        show_help
        ;;
esac