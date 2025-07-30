# AI Agent with "Computer Use" in a Virtual OS

This project demonstrates how to connect a simple web-based chat interface on a host machine (Windows) to a powerful AI agent running in a completely separate, isolated virtual machine (Ubuntu on VirtualBox).

The AI agent is not just a chatbot; it leverages the Anthropic Claude API to understand natural language commands, use "tools" to interact with its own operating system (e.g., run terminal commands), and formulate intelligent responses.

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

4.  **Install Python Dependencies:** With the environment active, install the required libraries, including a robust server engine like `eventlet` or `gevent`.
    ```bash
    pip install "Flask<3" "Flask-SocketIO<6" "python-engineio<5" "python-socketio<6" anthropic eventlet
    ```

5.  **Place and Modify the Code:** Create a `main.py` file. To ensure stability with tunneling, modify the SocketIO initialization to explicitly define the async mode:
    ```python
    # In main.py, change the SocketIO line to this:
    socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
    ```

6.  **Set the API Key:** Set your Anthropic API key as an environment variable. **This must be done every time you open a new terminal.**
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
3.  It will open in your default browser. The status should change from "Connecting..." to **"Connected"**.

You can now send commands like `list all files here` or `what is my current directory?` and receive responses from the AI agent running securely inside your virtual machine.

### Part 4: Automating Agent Startup (Inside the Ubuntu VM)

To avoid manually starting the agent every time, we can make it run automatically when you log in to your Ubuntu desktop.

1.  **Create a Startup Script:**
    * Open a **Terminal** in your Ubuntu VM.
    * Navigate to the directory containing your `main.py` and `myenv` folder.
    * Create a new script file: `nano start_agent.sh`
    * Paste the following content into the editor. **Crucially, replace the placeholder API key with your real one.**
    * Note: script may crash upon Ubuntu startup not finishing when it attempts to run. Temporary solution is to add a waiting time for the script to run to allow the Ubuntu to finish startup (e.g. sleep 10)

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
    * Save the file and exit `nano` (press `Ctrl+X`, then `Y`, then `Enter`).

2.  **Make the Script Executable:**
    * In the terminal, run this command to give the script permission to be executed:
        ```bash
        chmod +x start_agent.sh
        ```

3.  **Add to Startup Applications:**
    * Press the Super (Windows) key to open the applications menu.
    * Search for and open "Startup Applications".
    * Click **"Add"**.
    * Fill in the form:
        * **Name:** `AI Agent Starter`
        * **Command:** Click **"Browse..."** and select the `start_agent.sh` file you just created.
        * **Comment:** `Automatically starts the AI chat agent.`
    * Click **"Add"** to save.

4.  **Test the Automation:**
    * **Restart** your Ubuntu virtual machine.
    * After you log in, wait about 15 seconds.
    * Open the `chat.html` file on your Windows host. It should now connect successfully without you needing to run anything manually in the VM.

### Part 5: Deploying Frontend to the Cloud (Vercel) & Connecting via Tunnel

This section explains how to make your chat interface a public web app while keeping the AI agent running securely in your local VirtualBox.

1.  **Prepare the Frontend for Deployment:**
    * Vercel requires an `index.html` file in the root directory. In your PowerShell on Windows, navigate to your project folder and run:
        ```powershell
        # Move chat.html to the root and rename it
        mv chat-interface-frontend/chat.html .
        mv chat.html index.html
        ```

2.  **Create a Tunnel with `ngrok`:**
    * The `ngrok` service creates a secure public URL for your local server.
    * In a **Command Prompt** on Windows, run `ngrok` with the `--host-header` flag to ensure connection stability:
        ```cmd
        ngrok http 5000 --host-header=rewrite
        ```
    * `ngrok` will display a public `Forwarding` URL (e.g., `https://<random-string>.ngrok-free.app`). **Copy this URL.**

3.  **Update Frontend with Tunnel URL and Connection Fix:**
    * Open your `index.html` file.
    * Update the `agentUrl` constant with the `ngrok` URL you just copied.
    * **Crucially**, add `{ transports: ['websocket'] }` to the `io()` function. This forces a direct WebSocket connection, which is more stable through tunnels.
        ```javascript
        // Replace with your active ngrok URL
        const agentUrl = 'https://<random-string>.ngrok-free.app';

        // Force a direct WebSocket connection for stability
        const socket = io(agentUrl, { transports: ['websocket'] });
        ```

4.  **Push Changes to GitHub:**
    * Save your changes and commit them to your repository:
        ```bash
        git add .
        git commit -m "Feat: Prepare frontend for Vercel and tunneling"
        git push origin main
        ```

5.  **Deploy to Vercel:**
    * Go to [Vercel.com](https://vercel.com), create a new project, and import your `HishahK/ai-chat-project` repository.
    * Vercel will auto-detect the settings. Click **"Deploy"**.
    * Once finished, Vercel will give you a public URL for your web app.

Now, your Vercel web app will connect to your VirtualBox agent through the `ngrok` tunnel, allowing anyone to use your chat interface from anywhere.
