#!/bin/bash

# Start caffeinate in the background to prevent all types of sleep
caffeinate -d &
CAFFEINATE_PID=$!

# Function to check if the app is running
check_app() {
    pgrep -f "streamlit run app.py" > /dev/null
    return $?
}

# Function to start the app
start_app() {
    echo "Starting Streamlit app..."
    nohup streamlit run app.py > streamlit.log 2>&1 &
    echo $! > streamlit.pid
    
    # Wait a few seconds for Streamlit to start
    sleep 5
    
    # Extract and save the URL
    if [ -f streamlit.log ]; then
        URL=$(grep -o "http://[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+:[0-9]\+" streamlit.log | tail -n 1)
        if [ ! -z "$URL" ]; then
            echo "Streamlit is running at: $URL" > streamlit_url.txt
            echo "Streamlit is running at: $URL"
        fi
    fi
}

# Cleanup function
cleanup() {
    kill $CAFFEINATE_PID
    rm -f streamlit.pid streamlit.log streamlit_url.txt
    exit 0
}

# Set up trap for cleanup
trap cleanup EXIT

# Main loop
while true; do
    if ! check_app; then
        echo "App is not running. Starting..."
        start_app
    fi
    sleep 30  # Check every 30 seconds
done 