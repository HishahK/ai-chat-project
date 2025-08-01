# AI Agent with "Computer Use" and Virtual OS Sandbox

This project demonstrates how to connect a simple web-based chat interface on a host machine (Windows) to a powerful AI agent running in a completely separate, isolated virtual machine (Ubuntu on VirtualBox).

The AI agent is not just a chatbot; it leverages the Anthropic Claude API to understand natural language commands, use "tools" to interact with its own operating system (e.g., run terminal commands), and can display a live virtual Ubuntu desktop environment directly in the browser through an integrated VNC-based sandbox.

## Architecture Overview

The system consists of three main components that work together:

* **Frontend (Host Machine - Windows):** A single `chat.html` file that runs in any modern web browser. It uses HTML, Tailwind CSS, and JavaScript, connecting to the backend via WebSockets. Its only job is to send user messages and display AI responses.
* **Backend (Guest Machine - Ubuntu VM):** A Python server (`main.py`) using Flask and Flask-SocketIO. This is the "brain" of the operation. It receives messages, communicates with the Anthropic Claude API, and executes tools like bash commands within its own virtual environment.
* **The Connection (VirtualBox Port Forwarding):** This is the critical "bridge" between the host and the guest. We configure a rule in VirtualBox to forward any network traffic from a specific port on the Windows host (`localhost:5000`) to the same port inside the Ubuntu VM. This makes the backend server, which is isolated inside the VM, accessible to the frontend running on Windows.

**Communication Flow:**
> Browser (Windows) ➔ `localhost:5000` ➔ VirtualBox Port Forwarding Rule ➔ Ubuntu VM Port 5000 ➔ Python AI Agent

---

## Setup and Installation Guide

Follow these steps precisely to replicate the environment.

### Part 1: Setting Up the Virtual Machine (VirtualBox)

1.  **Install VirtualBox:** Download and install the latest version of VirtualBox on your Windows host machine.
2.  **Create an Ubuntu VM:**
    * Download the Ubuntu Desktop LTS ISO file from the official Ubuntu website.
    * In VirtualBox, create a new virtual machine, selecting the downloaded ISO.
    * Allocate at least 4GB of RAM and 2 CPU cores for smooth performance.
    * Complete the Ubuntu installation process inside the VM.
3.  **Configure Port Forwarding (The Crucial Step):**
    * Shut down the Ubuntu VM completely (status must be "Powered Off").
    * Open Command Prompt (CMD) as an Administrator on your Windows machine.
    * Run the following command to manually create the port forwarding rule. This method is more reliable than the GUI.
        ```cmd
        "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" modifyvm "Your-VM-Name" --natpf1 "ai-agent,tcp,,5000,,5000"
        ```
    > **Note:** Replace `"Your-VM-Name"` with the exact name of your virtual machine in VirtualBox (e.g., "Ubuntu AI Agent").

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
    > You will see `(myenv)` at the beginning of your terminal prompt.
4.  **Install Python Dependencies:** With the environment active, install the required libraries, including a robust server engine like `eventlet` or `gevent`.
    ```bash
    pip install "Flask<3" "Flask-SocketIO<6" "python-engineio<5" "python-socketio<6" anthropic eventlet
    ```
5.  **Place and Modify the Code:** Create a `main.py` file. To ensure stability with tunneling, modify the `SocketIO` initialization to explicitly define the async mode:
    ```python
    # In main.py, change the SocketIO line to this:
    socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
    ```
6.  **Set the API Key:** Set your Anthropic API key as an environment variable. This must be done every time you open a new terminal.
    ```bash
    export ANTHROPIC_API_KEY='your-anthropic-api-key-goes-here'
    ```
7.  **Run the Server:**
    ```bash
    python3 main.py
    ```
    The server is now running inside the VM and listening on port 5000.

### Part 3: Running the Frontend (Locally on Windows Host)

1.  Navigate to the `chat-interface-frontend` folder on your Windows machine.
2.  Double-click the `chat.html` file.
3.  It will open in your default browser. The status should change from **"Connecting..."** to **"Connected"**.
4.  You can now send commands like `list all files here` or `what is my current directory?` and receive responses from the AI agent running securely inside your virtual machine.

### Part 4: Automating Agent Startup (Inside the Ubuntu VM)

To avoid manually starting the agent every time, we can make it run automatically when you log in to your Ubuntu desktop.

1.  **Create a Startup Script:**
    * Open a Terminal in your Ubuntu VM.
    * Navigate to the directory containing your `main.py` and `myenv` folder.
    * Create a new script file: `nano start_agent.sh`
    * Paste the following content into the editor. Crucially, replace the placeholder API key with your real one.
        > **Note:** The script may crash if Ubuntu startup hasn't finished when it attempts to run. A temporary solution is to add a waiting time (`sleep 10`) to allow the OS to finish loading.
    ```bash
    #!/bin/bash

    # wait for a few seconds to allow Ubuntu to finish startup
    sleep 10

    # Set the API Key
    export ANTHROPIC_API_KEY='your-real-anthropic-api-key-goes-here'

    # Navigate to the project directory.
    # IMPORTANT: Change '/home/vboxuser/Desktop' if your project is elsewhere.
    cd /home/vboxuser/Desktop/

    # Activate the Python virtual environment
    source myenv/bin/activate

    # Run the Python agent server
    python3 main.py
    ```
    * Save the file and exit nano (press `Ctrl+X`, then `Y`, then `Enter`).

2.  **Make the Script Executable:**
    In the terminal, run this command to give the script permission to be executed:
    ```bash
    chmod +x start_agent.sh
    ```
3.  **Add to Startup Applications:**
    * Press the `Super` (Windows) key to open the applications menu.
    * Search for and open "Startup Applications".
    * Click "Add".
    * Fill in the form:
        * **Name:** AI Agent Starter
        * **Command:** Click "Browse..." and select the `start_agent.sh` file you just created.
        * **Comment:** Automatically starts the AI chat agent.
    * Click "Add" to save.
4.  **Test the Automation:**
    * Restart your Ubuntu virtual machine.
    * After you log in, wait about 15 seconds.
    * Open the `chat.html` file on your Windows host. It should now connect successfully without you needing to run anything manually in the VM.

### Part 5: Deploying Frontend to the Cloud (Vercel) & Connecting via Tunnel

This section explains how to make your chat interface a public web app while keeping the AI agent running securely in your local VirtualBox.

1.  **Prepare the Frontend for Deployment:**
    Vercel requires an `index.html` file in the root directory. In your PowerShell on Windows, navigate to your project folder and run:
    ```powershell
    # Move chat.html to the root and rename it
    mv chat-interface-frontend/chat.html .
    mv chat.html index.html
    ```
2.  **Create a Tunnel with ngrok:**
    The `ngrok` service creates a secure public URL for your local server.
    In a Command Prompt on Windows, run ngrok with the `--host-header` flag to ensure connection stability:
    ```cmd
    ngrok http 5000 --host-header=rewrite
    ```
    `ngrok` will display a public **Forwarding URL** (e.g., `https://<random-string>.ngrok-free.app`). Copy this URL.

3.  **Update Frontend with Tunnel URL and Connection Fix:**
    * Open your `index.html` file.
    * Update the `agentUrl` constant with the ngrok URL you just copied.
    * Crucially, add `{ transports: ['websocket'] }` to the `io()` function. This forces a direct WebSocket connection, which is more stable through tunnels.
    ```javascript
    // Replace with your active ngrok URL
    const agentUrl = 'https://<random-string>.ngrok-free.app';

    // Force a direct WebSocket connection for stability
    const socket = io(agentUrl, { transports: ['websocket'] });
    ```
4.  **Push Changes to GitHub:**
    Save your changes and commit them to your repository:
    ```bash
    git add .
    git commit -m "Feat: Prepare frontend for Vercel and tunneling"
    git push origin main
    ```
5.  **Deploy to Vercel:**
    * Go to Vercel.com, create a new project, and import your repository.
    * Vercel will auto-detect the settings. Click "Deploy".
    * Once finished, Vercel will give you a public URL for your web app.

### Part 6: Setting Up Virtual OS Sandbox (VNC Desktop Environment)

This step enables the AI agent to display a live Ubuntu desktop environment directly in the browser when requested.

1.  **Install VNC and Desktop Components:**
    ```bash
    sudo apt update
    sudo apt install tigervnc-standalone-server fluxbox xterm xclock websockify novnc
    ```
2.  **Configure VNC Authentication:**
    ```bash
    vncpasswd
    # Set a password when prompted
    ```
3.  **Create VNC Startup Script:**
    ```bash
    cat > ~/.vnc/xstartup << 'EOF'
    #!/bin/bash
    unset SESSION_MANAGER
    unset DBUS_SESSION_BUS_ADDRESS
    exec fluxbox
    EOF
    chmod +x ~/.vnc/xstartup
    ```
4.  **Create Automated VNC Startup Script:**
    ```bash
    cat > ~/start_vnc.sh << 'EOF'
    #!/bin/bash
    export DISPLAY=:3
    Xtigervnc :3 -desktop "Ubuntu Desktop" -geometry 1024x768 -depth 24 -rfbport 5903 -SecurityTypes=None &
    sleep 3
    fluxbox &
    xterm -geometry 80x24+10+10 &
    xclock -geometry 150x150+200+10 &
    websockify --web=/usr/share/novnc/ 6080 localhost:5903 &
    EOF
    chmod +x ~/start_vnc.sh
    ```
5.  **Install and Configure ngrok (inside VM):**
    ```bash
    sudo snap install ngrok
    ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
    ```
6.  **Test the Sandbox:**
    * Run `~/start_vnc.sh` to start the VNC environment.
    * Deploy your chat interface and ask the AI agent: `start virtual os sandbox`.
    * The Ubuntu desktop should appear in the sandbox panel of your web interface.

Now, your Vercel web app will connect to your VirtualBox agent through the ngrok tunnel, allowing anyone to use your chat interface from anywhere with full virtual OS sandbox capabilities.