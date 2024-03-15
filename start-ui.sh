#!/bin/bash

# Define colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # Clear color.

# Display Super-Cool project title.
fancy_project_title() {
    echo -e "
\033[38;05;196m  _     __  __ ____        ____    _____ _____ \033[0m
\033[38;05;208;1m | |   |  \/  |  _ \ ___  / ___|  |  ___| ____|\033[0m
\033[38;05;220;1m | |   | |\/| | |_) / _ \| |      | |_  |  _|  \033[0m
\033[38;05;82;1m | |___| |  | |  __/ (_) | |___   |  _| | |___ \033[0m
\033[38;05;33;1m |_____|_|  |_|_|   \___/ \____|  |_|   |_____|\033[0m
${NC}
"
}

fancy_project_title
#

python_version_check() {
    required_python_version="3.11.0"
    current_python_version=$(python3 --version 2>&1 | awk '{print $2}')
    if [[ "$(printf '%s\n' "$required_python_version" "$current_python_version" | sort -V | head -n1)" != "$required_python_version" ]]; then
        printf "${YELLOW}Warning: Python version is ${current_python_version}. Expected ${required_python_version} or newer.${NC}\n"
    else
        printf "${GREEN}Python version ${current_python_version} meets the requirement.${NC}\n"
    fi
}

create_venv() {
    printf "${YELLOW}Creating Python virtual environment in .venv folder...${NC}\n"
    if python3 -m venv .venv; then
        printf "${GREEN}Virtual environment created successfully.${NC}\n"
    else
        printf "${RED}Failed to create virtual environment.${NC}\n"
        exit 1
    fi
}

activate_venv() {
    printf "${YELLOW}Activating virtual environment...${NC}\n"
    source .venv/bin/activate
    if [[ $? -ne 0 ]]; then
        printf "${RED}Failed to activate virtual environment.${NC}\n"
        exit 1
    else
        printf "${GREEN}Virtual environment activated.${NC}\n"
    fi
}

install_requirements() {
    printf "${YELLOW}Installing requirements...${NC}\n"
    if ! pip install --disable-pip-version-check -q -r requirements.txt; then
        printf "${RED}Failed to install required packages.${NC}\n"
        exit 1
    else
        printf "${GREEN}All required packages installed.${NC}\n"
    fi
}

run_streamlit_webui() {
    printf "\n${GREEN}Starting Streamlit web UI...${NC}\n"
    if ! streamlit run webui.py --browser.gatherUsageStats False --server.address "0.0.0.0"; then
        printf "${RED}Failed to start Streamlit web UI.${NC}\n"
        exit 1
    fi
}


# Function to install dependencies on Ubuntu
install_ubuntu_dependencies() {
    printf "${CYAN}Checking for required build tools on Ubuntu...${NC}\n"
    # Update package lists to ensure accurate checks
    sudo apt-get update

    # Check if build-essential is installed
    if ! dpkg -l | grep -qw build-essential; then
        printf "${YELLOW}Installing build-essential...${NC}\n"
        if ! sudo apt-get install -y build-essential; then
            printf "${RED}Failed to install build-essential.${NC}\n"
            exit 1
        fi
    else
        printf "${GREEN}build-essential is already installed.${NC}\n"
    fi

    # Check if gcc is installed
    if ! dpkg -l | grep -qw gcc; then
        printf "${YELLOW}Installing gcc...${NC}\n"
        if ! sudo apt-get install -y gcc; then
            printf "${RED}Failed to install gcc.${NC}\n"
            exit 1
        fi
    else
        printf "${GREEN}gcc is already installed.${NC}\n"
    fi
}

# Function to handle macOS dependencies
install_macos_dependencies() {
    printf "${CYAN}Checking for required build tools on macOS...${NC}\n"
    # Xcode Command Line Tools includes gcc and make
    if ! xcode-select -p &>/dev/null; then
        printf "${YELLOW}Installing Xcode Command Line Tools...${NC}\n"
        if ! xcode-select --install &>/dev/null; then
            printf "${RED}Failed to initiate installation of Xcode Command Line Tools.${NC}\n"
            exit 1
        fi
    else
        printf "${GREEN}Xcode Command Line Tools are already installed.${NC}\n"
    fi
}

get_os_type() {
    OS="$(uname)"
    case $OS in
        Linux)
            if [[ -f /etc/os-release && "$(grep '^ID=' /etc/os-release)" == *"ubuntu"* ]]; then
                install_ubuntu_dependencies
            else
                printf "${YELLOW}Non-Ubuntu Linux detected. Please ensure build dependencies are installed.${NC}\n"
            fi
            ;;
        Darwin)
            install_macos_dependencies
            ;;
        *)
            printf "${RED}Unsupported operating system: ${OS}.${NC}\n"
            exit 1
            ;;
    esac
}

# Main execution starts here
get_os_type
python_version_check
if [ ! -d ".venv" ]; then
    create_venv
fi

activate_venv
install_requirements
run_streamlit_webui
