# Local AI Agent with OS Control

This project demonstrates how to build an AI agent that runs in an isolated VirtualBox VM (Ubuntu) but is controlled by a simple web interface on the host machine (Windows). The agent uses the Anthropic Claude API to understand commands, execute tools like shell scripts within its own OS, and can even stream a live VNC desktop sandbox directly to the browser.

---

## How It Works

The system is composed of a frontend, a backend, and the network bridge that connects them.

* **Frontend (Host - Windows):** A single `chat.html` file that serves as the user interface, communicating with the backend via WebSockets.
* **Backend (Guest - Ubuntu VM):** A Python server using Flask-SocketIO. It acts as the agent's "brain," processing commands, interacting with the Claude API, and executing tools within the Ubuntu environment.
* **Connection (VirtualBox Port Forwarding):** A network rule forwards traffic from `localhost:5000` on the Windows host to port `5000` inside the Ubuntu VM, making the isolated backend accessible to the host's browser.

**Communication Flow:**
> Browser (Windows) ➔ `localhost:5000` ➔ VirtualBox Port Forwarding ➔ Ubuntu VM Port 5000 ➔ Python AI Agent

---

## Prerequisites

Before you begin, ensure you have the following:

* **VirtualBox:** The latest version installed on your Windows host.
* **Ubuntu Desktop ISO:** The latest LTS version is recommended.
* **Anthropic API Key:** You will need a valid API key for the agent to function.
* **(Optional) ngrok Account:** Required only if you plan to deploy the frontend to the cloud.

---

## Installation

### Step 1: Configure the Virtual Machine

1.  **Create an Ubuntu VM:** In VirtualBox, create a new virtual machine using the downloaded Ubuntu ISO. Allocate at least 4GB of RAM and 2 CPU cores.
2.  **Configure Port Forwarding:** Shut down the VM completely. Open **Command Prompt as an Administrator** on Windows and run the following command. This is the crucial step that connects the host to the guest VM.

    ```cmd
    "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" modifyvm "Your-VM-Name" --natpf1 "ai-agent,tcp,,5000,,5000"
    ```
    > **Note:** Replace `"Your-VM-Name"` with the exact name of your VM in VirtualBox.

### Step 2: Set Up the Backend in Ubuntu

1.  **Start the Ubuntu VM** and open a **Terminal**.
2.  **Create a Python Virtual Environment:** This isolates our project's dependencies from the system's Python installation.
    ```bash
    # Install the necessary tool
    sudo apt update
    sudo apt install python3-venv

    # Create and activate the environment
    python3 -m venv myenv
    source myenv/bin/activate
    ```
    > Your terminal prompt should now be prefixed with `(myenv)`.

3.  **Install Python Dependencies:**
    ```bash
    pip install "Flask<3" "Flask-SocketIO<6" "python-engineio<5" "python-socketio<6" anthropic eventlet
    ```
4.  **Place and Configure the Code:**
    * Create a `main.py` file for the backend server.
    * To ensure stability, modify the `SocketIO` initialization to explicitly define the async mode:
        ```python
        # In main.py
        socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
        ```
---

## Environment Variables

The AI agent requires your Anthropic API key to be set as an environment variable within the Ubuntu VM.

1.  **Set the API Key:** In your activated `(myenv)` terminal, run the following command.
    > **Note:** This variable must be set every time you open a new terminal session unless you configure the startup automation.
    ```bash
    export ANTHROPIC_API_KEY='your-anthropic-api-key-goes-here'
    ```

---

## Usage

1.  **Start the Backend Server:** In the Ubuntu VM's terminal (with the virtual environment activated and API key set), run the server:
    ```bash
    python3 main.py
    ```
    The agent is now running inside the VM and listening for connections.

2.  **Launch the Frontend:** On your Windows host machine, navigate to the project folder and double-click the `chat.html` file. It will open in your browser, and the status should change to **"Connected"**.

3.  **Interact with the Agent:** You can now send commands like `list all files in the current directory` or `what is my user name?`.

---

## Advanced Configuration

### Automating Agent Startup on Login

To avoid manually starting the server every time, you can configure it to launch automatically when you log into the Ubuntu desktop.

1.  **Create a Startup Script:** In the Ubuntu VM, create a file named `start_agent.sh` and add the following content. **Remember to replace the placeholder API key and directory path.**

    ```bash
    #!/bin/bash

    # Wait for the desktop environment to load
    sleep 10

    # Set the API Key
    export ANTHROPIC_API_KEY='your-real-anthropic-api-key-goes-here'

    # Navigate to your project directory (IMPORTANT: Change if necessary)
    cd /home/vboxuser/your-project-folder/

    # Activate the Python virtual environment
    source myenv/bin/activate

    # Run the Python agent server
    python3 main.py
    ```

2.  **Make the Script Executable:**
    ```bash
    chmod +x start_agent.sh
    ```

3.  **Add to Startup Applications:**
    * Press the `Super` (Windows) key and search for "Startup Applications".
    * Click **Add** and set the **Command** field by Browse to your `start_agent.sh` script.

### Deploying Frontend to the Cloud (Vercel)

This allows you to access your chat interface from a public URL while the agent remains secure in your local VM.

1.  **Create a Tunnel with ngrok:** On your **Windows host**, run ngrok to expose your local port `5000` to the internet.
    ```cmd
    ngrok http 5000 --host-header=rewrite
    ```
    Copy the public **Forwarding URL** (e.g., `https://<random-string>.ngrok-free.app`).

2.  **Update Frontend for Tunneling:**
    * Open your `chat.html` file (or `index.html`).
    * Update the `agentUrl` constant with your ngrok URL.
    * **Crucially**, modify the `io()` function to force a direct WebSocket connection, which is required for stability through tunnels.
    ```javascript
    // Replace with your active ngrok URL
    const agentUrl = 'https://<random-string>.ngrok-free.app';

    // Force a direct WebSocket connection
    const socket = io(agentUrl, { transports: ['websocket'] });
    ```

3.  **Deploy to Vercel:** Push your updated frontend code to a GitHub repository and import it into Vercel. Vercel will build and deploy it, giving you a public URL to your chat app.

### Setting Up the Virtual OS Sandbox (VNC)

This enables the agent to display a live Ubuntu desktop inside the chat interface. Run these commands inside the **Ubuntu VM**.

1.  **Install VNC Components:**
    ```bash
    sudo apt update
    sudo apt install tigervnc-standalone-server fluxbox xterm xclock websockify novnc
    ```
2.  **Configure VNC Password:**
    ```bash
    vncpasswd
    ```
3.  **Configure VNC Startup:**
    ```bash
    mkdir -p ~/.vnc
    cat > ~/.vnc/xstartup << 'EOF'
    #!/bin/bash
    unset SESSION_MANAGER
    unset DBUS_SESSION_BUS_ADDRESS
    exec fluxbox
    EOF
    chmod +x ~/.vnc/xstartup
    ```
4.  **Create a VNC Server Script (`start_vnc.sh`):**
    ```bash
    cat > ~/start_vnc.sh << 'EOF'
    #!/bin/bash
    export DISPLAY=:3
    # Start the VNC server without a password prompt for the agent
    Xtigervnc :3 -desktop "Ubuntu Sandbox" -geometry 1024x768 -depth 24 -rfbport 5903 -SecurityTypes=None &
    sleep 3
    # Start the window manager and some apps
    fluxbox &
    xterm &
    # Start the WebSocket proxy for noVNC
    websockify --web=/usr/share/novnc/ 6080 localhost:5903 &
    EOF
    chmod +x ~/start_vnc.sh
    ```
    > You can now have the AI agent run this script (e.g., `bash ~/start_vnc.sh`) to start the sandbox. You will need to configure a separate `ngrok` tunnel for port `6080` to expose the VNC viewer.