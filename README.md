# AI Agent with "Computer Use" in a Virtual OS

This project demonstrates how to connect a simple web-based chat interface on a host machine (Windows) to a powerful AI agent running in a completely separate, isolated virtual machine (Ubuntu on VirtualBox).

The AI agent is not just a chatbot; it leverages the Anthropic Claude API to understand natural language commands, use "tools" to interact with its own operating system (e.g., run terminal commands), and formulate intelligent responses.

---

## Architecture Overview

The system consists of three main components that work together:

1.  **Frontend (Host Machine - Windows):**
    * A single `chat.html` file that runs in any modern web browser.
    * Uses HTML, Tailwind CSS, and JavaScript.
    * Connects to the backend via WebSockets (`Socket.IO`).
    * Its only job is to send user messages and display AI responses.

2.  **Backend (Guest Machine - Ubuntu VM):**
    * A Python server (`main.py`) using Flask and Flask-SocketIO.
    * This is the "brain" of the operation.
    * It receives messages, communicates with the Anthropic Claude API, and executes tools like bash commands within its own virtual environment.

3.  **The Connection (VirtualBox Port Forwarding):**
    * This is the critical "bridge" between the host and the guest.
    * We configure a rule in VirtualBox to forward any network traffic from a specific port on the Windows host (`localhost:5000`) to the same port inside the Ubuntu VM.
    * This makes the backend server, which is isolated inside the VM, accessible to the frontend running on Windows.

**Communication Flow:**
`Browser (Windows)` ➔ `localhost:5000` ➔ `VirtualBox Port Forwarding Rule` ➔ `Ubuntu VM Port 5000` ➔ `Python AI Agent`

---

## Setup and Installation Guide

Follow these steps precisely to replicate the environment.

### Part 1: Setting Up the Virtual Machine (VirtualBox)

1.  **Install VirtualBox:** Download and install the latest version of [VirtualBox](https://www.virtualbox.org/wiki/Downloads) on your Windows host machine.

2.  **Create an Ubuntu VM:**
    * Download the **Ubuntu Desktop LTS** ISO file from the [official Ubuntu website](https://ubuntu.com/download/desktop).
    * In VirtualBox, create a new virtual machine, selecting the downloaded ISO.
    * Allocate at least 4GB of RAM and 2 CPU cores for smooth performance.
    * Complete the Ubuntu installation process inside the VM.

3.  **Configure Port Forwarding (The Crucial Step):**
    * **Shut down** the Ubuntu VM completely (status must be "Powered Off").
    * Open **Command Prompt (CMD) as an Administrator** on your Windows machine.
    * Run the following command to manually create the port forwarding rule. This method is more reliable than the GUI.
        ```cmd
        "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" modifyvm "Your-VM-Name" --natpf1 "ai-agent,tcp,,5000,,5000"
        ```
    * **Note:** Replace `"Your-VM-Name"` with the exact name of your virtual machine in VirtualBox (e.g., "Ubuntu AI Agent").

### Part 2: Setting Up the AI Agent Backend (Inside the Ubuntu VM)

1.  **Start the Ubuntu VM.**

2.  **Open a Terminal** inside the Ubuntu desktop.

3.  **Create a Python Virtual Environment:** Ubuntu protects its system Python. We must create a self-contained environment for our project.
    ```bash
    # Install the tool to create virtual environments
    sudo apt update
    sudo apt install python3-venv

    # Create a virtual environment named "myenv"
    python3 -m venv myenv

    # Activate the environment (you must do this every time you open a new terminal)
    source myenv/bin/activate
    ```
    You will see `(myenv)` at the beginning of your terminal prompt.

4.  **Install Python Dependencies:** With the environment active, install the required libraries.
    ```bash
    pip install "Flask<3" "Flask-SocketIO<6" "python-engineio<5" "python-socketio<6" anthropic
    ```

5.  **Place the Code:** Create a `main.py` file and paste the backend Python code into it.

6.  **Set the API Key:** Set your Anthropic API key as an environment variable. **This must be done every time you open a new terminal.**
    ```bash
    export ANTHROPIC_API_KEY='your-anthropic-api-key-goes-here'
    ```

7.  **Run the Server:**
    ```bash
    python3 main.py
    ```
    The server is now running inside the VM and listening on port 5000.

### Part 3: Running the Frontend (On the Windows Host)

1.  Navigate to the `chat-interface-frontend` folder on your Windows machine.
2.  Double-click the `chat.html` file.
3.  It will open in your default browser. The status should change from "Connecting..." to **"Connected"**.

You can now send commands like `list all files here` or `what is my current directory?` and receive responses from the AI agent running securely inside your virtual machine.


### Part 4: Automating the Agent on Startup

To avoid having to run the agent manually every time the virtual machine is started, we can configure it to run automatically upon login. This method uses Ubuntu's built-in "Startup Applications" feature.

This process involves creating a startup script which is then registered to run when the desktop starts.

Step 1: Create the Startup Script
This script will contain all the commands we would normally type manually in the terminal.

Inside the Ubuntu VM, open a Terminal and create a new file named start_agent.sh (e.g., on the Desktop).

nano ~/Desktop/start_agent.sh

Copy and paste the following content into the file. Be sure to replace the placeholder API key and username (vboxuser) if necessary.

#!/bin/bash

# AI AGENT STARTUP SCRIPT 
# This script will be executed in a new terminal upon startup.

# 1. Wait for 10 seconds to allow the system (especially the network) to fully initialize. This part is a translated version of the script we utilized for documentation purposes
echo "Waiting 10 seconds for the system to be ready..."
sleep 10

# 2. Set the Anthropic API Key.
# Replace 'your-anthropic-api-key-goes-here' with your actual API key.
echo "Setting API Key..."
export ANTHROPIC_API_KEY='your-anthropic-api-key-goes-here'

# 3. Navigate to the project directory (use the full path).
# Replace 'vboxuser' with your username in the VM if it's different.
echo "Changing to project directory..."
cd /home/vboxuser/Desktop/

# 4. Activate the Python virtual environment (use the full path).
echo "Activating virtual environment..."
source /home/vboxuser/Desktop/myenv/bin/activate

# 5. Run the AI agent server.
echo "Running AI Agent server..."
python3 main.py

# This command keeps the terminal window from closing immediately
# if the script finishes or encounters an error, so we can see the messages.
exec bash

Save the file (Ctrl+X, then Y, then Enter).

Step 2: Make the Script Executable
We need to grant permission for this file to be run as a program.

chmod +x ~/Desktop/start_agent.sh

Step 3: Register with Startup Applications
Open the Ubuntu applications menu and search for "Startup Applications".

Click "Add" to create a new entry.

Fill out the form as follows:

Name: AI Agent Starter

Command: gnome-terminal -- /home/vboxuser/Desktop/start_agent.sh

This command tells the system to open a new terminal window and then run our script inside it. This is important for debugging and ensuring the script runs correctly.

Comment: Starts the Python AI agent for the chat interface.

Click "Save".

Result
Now, every time you restart the virtual machine and log in, a terminal window will appear automatically and run the AI agent server. After a few seconds, the frontend in your Windows browser will be able to connect without any manual intervention.
