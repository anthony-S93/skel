#!/bin/sh

if [ "$(id -u)" = 0 ]
then
    echo "The setup script should not be run with sudo."
    echo "Aborting."
    exit 1
fi

skel_home="$(dirname "$(readlink -f "$0")")"
virtual_env="$skel_home/.venv"

report_broken_venv() {
    echo "Something is wrong with the virtual environment."
    echo "Delete the \"$virtual_env\" directory and try again."
    exit 1
}

if [ ! -d "$virtual_env" ]
then
    # Create virtual environment
    echo "Creating virtual environment..."
    if python -m venv "$virtual_env"
    then
        echo "Virtual environment created at \"$virtual_env\""
    else
        echo "Cannot create virtual environment."
        echo "Aborting"
        exit 1
    fi
else
    if [ ! -f "$virtual_env/bin/activate" ]
    then
        # Missing activation script
        echo "The activation script for the virtual environment is missing."
        report_broken_venv
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
. "$virtual_env/bin/activate"
echo "Virtual environment activated."

# Install dependencies 
if command -v pip > /dev/null 2>&1
then
    echo "Installing dependencies..."
    pip install -r "$skel_home/requirements.txt"
else
    # Pip should be available once the virtual environment is activated
    echo "The executable for 'pip' is missing."
    report_broken_venv
fi

chmod +x "$skel_home/bin/skel"
echo ""
echo "Setup complete."
