#!/bin/bash

# uPNP Volume Control Management Script
# Trisha's favorite script for making things happen!

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Colorful logging because life's too short for boring logs
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VENV_PATH="$PROJECT_ROOT/.venv"
PYTHON_BIN="$VENV_PATH/bin/python"
APP_SCRIPT="$PROJECT_ROOT/src/menu_bar_app.py"
PID_FILE="$PROJECT_ROOT/upnp_volume_control.pid"

create_venv() {
    echo -e "${GREEN} Magical Virtual Environment Creation ${NC}"
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip
    pip install -r "$PROJECT_ROOT/requirements.txt"
    
    # Install PyQt6 system dependencies if needed
    if ! python -c "import PyQt6" &> /dev/null; then
        echo -e "${GREEN} Installing PyQt6 dependencies...${NC}"
        brew install qt@6
    fi
}

start_service() {
    if [ -f "$PID_FILE" ]; then
        echo -e "${RED} Service already running! Check $PID_FILE${NC}"
        exit 1
    fi

    echo -e "${GREEN} Launching uPNP Volume Control Menu Bar App${NC}"
    source "$VENV_PATH/bin/activate"
    "$PYTHON_BIN" "$APP_SCRIPT" & 
    echo $! > "$PID_FILE"
    echo -e "${GREEN} App started with PID $(cat $PID_FILE)${NC}"
}

stop_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo -e "${RED} Stopping uPNP Volume Control App${NC}"
        kill "$PID"
        rm "$PID_FILE"
        echo -e "${GREEN} App stopped${NC}"
    else
        echo -e "${RED} No app running${NC}"
    fi
}

case "$1" in 
    create-venv)
        create_venv
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        start_service
        ;;
    *)
        echo "Usage: $0 {create-venv|start|stop|restart}"
        exit 1
esac

exit 0
