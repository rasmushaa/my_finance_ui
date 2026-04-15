#!/bin/bash

# How To Run:
# 1. Provide execution permissions to the shell script by running: chmod +x init_bigquery_database.sh
# 2. Run: bash run_dev.sh
# 3. Previous Running Streamlit is terminated, and a new streamlit is created

# Function to kill any running Streamlit process
kill_previous_streamlit() {
    echo ""
    echo "Checking for running Streamlit instances..."
    # Find the process running on port  and kill it
    PID=$(lsof -ti:8080)  # Get the process ID for port 8080
    if [ -n "$PID" ]; then
        echo "Killing previous Streamlit process (PID: $PID)..."
        kill -9 $PID
    else
        echo "No running Streamlit instance found."
    fi
}


# Function to load environment variables from .env file
load_env() {
    echo "Loading environment variables from .env..."
    if [ -f .env ]; then
        # Read the .env.dev file line by line
        while IFS= read -r line; do
            # Skip comments and empty lines
            [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
            # Export the variable
            export "$line"
        done < .env
    else
        echo ".env file not found."
    fi
}


run_dev() {
    kill_previous_streamlit
    echo "Running in DEV environment..."
    load_env
    PYTHONPATH="$PWD" uv run streamlit run src/app.py --server.port 8080 --server.headless=true
}


run_dev