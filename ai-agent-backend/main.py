import os
import subprocess
import json
import time
from flask import Flask, request
from flask_socketio import SocketIO, emit
import anthropic
from pyngrok import ngrok, conf

conf.get_default().auth_token = "30UGDKralWxXQyYwj4BVvKAsmqk_4gTnMCwJBUrdNi24SAs14"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'computer-agent-secret-v3'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", logger=True, engineio_logger=True)

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
   print("Error: Environment variable ANTHROPIC_API_KEY not found.")
   exit()
client = anthropic.Anthropic(api_key=api_key)

sandbox_active = False

def run_bash_command(command):
   print(f"TOOLBOX: Running bash command: {command}")
   try:
       result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
       return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
   except subprocess.CalledProcessError as e:
       return f"Error running command:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
   except subprocess.TimeoutExpired:
       return "Error: Command execution timeout (30 seconds)."

def start_virtual_os_sandbox(vm_name="UbuntuAIAgent"):
   global sandbox_active
   print(f"TOOLBOX: Starting sandbox for VM: {vm_name}")
   HOST_PORT_VNC = 6080
   try:
       for tunnel in ngrok.get_tunnels():
           if tunnel.config['addr'].endswith(str(HOST_PORT_VNC)):
               print(f"Closing existing ngrok tunnel: {tunnel.public_url}")
               ngrok.disconnect(tunnel.public_url)
       
       subprocess.run("pkill -f 'Xtigervnc :3'", shell=True)
       subprocess.run("pkill -f 'websockify'", shell=True)
       time.sleep(2)
       
       subprocess.Popen("export DISPLAY=:3 && Xtigervnc :3 -desktop 'Ubuntu Desktop' -geometry 1024x768 -depth 24 -rfbport 5903 -SecurityTypes=None", shell=True)
       time.sleep(3)
       subprocess.Popen("DISPLAY=:3 fluxbox &", shell=True)
       subprocess.Popen("DISPLAY=:3 xterm -geometry 80x24+10+10 &", shell=True)
       subprocess.Popen("DISPLAY=:3 xclock -geometry 150x150+200+10 &", shell=True)
       subprocess.Popen(f"websockify --web=/usr/share/novnc/ {HOST_PORT_VNC} localhost:5903", shell=True)
       time.sleep(2)
       
       print(f"Opening ngrok tunnel to http://localhost:{HOST_PORT_VNC}...")
       tunnel = ngrok.connect(HOST_PORT_VNC, "http")
       public_url = tunnel.public_url
       print(f"Ngrok tunnel created successfully: {public_url}")
       vnc_view_url = f"{public_url}/vnc.html?host={tunnel.public_url.split('//')[1].split(':')[0]}&port=443&encrypt=1&path=websockify"
       
       sandbox_active = True
       result = {"status": "success", "message": f"Sandbox for {vm_name} started successfully.", "vnc_view_url": vnc_view_url}
       print(f"EMITTING SANDBOX VIEW: {result}")
       socketio.emit('sandbox_view', result)
       return json.dumps(result)
   except Exception as e:
       error_result = {"status": "error", "message": f"Unexpected error occurred: {str(e)}"}
       print(f"EMITTING ERROR: {error_result}")
       socketio.emit('sandbox_view', error_result)
       return json.dumps(error_result)

def should_auto_start_sandbox(user_message):
    triggers = [
        "open", "browse", "website", "gui", "desktop", "visual", 
        "click", "screenshot", "window", "application", "install",
        "download", "file manager", "browser", "editor", "show",
        "firefox", "chrome", "nautilus", "gedit", "calculator",
        "image", "picture", "photo", "video", "media", "display",
        "start", "launch", "run app", "open app", "view", "see",
        "virtual", "sandbox", "os"
    ]
    message_lower = user_message.lower()
    return any(trigger in message_lower for trigger in triggers)

def analyze_user_intent(user_message):
    desktop_keywords = {
        'visual': ['screenshot', 'see', 'show', 'display', 'visual', 'gui', 'window'],
        'web': ['browse', 'website', 'google', 'search web', 'open browser', 'firefox', 'chrome'],
        'files': ['file manager', 'folder', 'download', 'upload', 'documents', 'nautilus'],
        'apps': ['install', 'application', 'software', 'program', 'open app', 'calculator', 'gedit'],
        'sandbox': ['virtual', 'sandbox', 'desktop', 'os', 'environment']
    }
    
    message_lower = user_message.lower()
    needs_desktop = False
    intent_category = 'terminal'
    
    for category, keywords in desktop_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            needs_desktop = True
            intent_category = category
            break
    
    return {
        'needs_desktop': needs_desktop,
        'category': intent_category
    }

def enhance_command_for_gui(user_message, intent):
    if intent['category'] == 'web':
        if 'firefox' in user_message.lower():
            return "DISPLAY=:3 firefox &"
        elif 'chrome' in user_message.lower():
            return "DISPLAY=:3 google-chrome &"
        elif 'browse' in user_message.lower() or 'website' in user_message.lower():
            return "DISPLAY=:3 firefox &"
    
    elif intent['category'] == 'files':
        return "DISPLAY=:3 nautilus &"
    
    elif intent['category'] == 'apps':
        if 'calculator' in user_message.lower():
            return "DISPLAY=:3 gnome-calculator &"
        elif 'editor' in user_message.lower() or 'gedit' in user_message.lower():
            return "DISPLAY=:3 gedit &"
        elif 'install' in user_message.lower():
            app_name = extract_app_name(user_message)
            return f"sudo apt update && sudo apt install -y {app_name}"
    
    return None

def extract_app_name(message):
    words = message.lower().split()
    if 'install' in words:
        install_idx = words.index('install')
        if install_idx + 1 < len(words):
            return words[install_idx + 1]
    return 'firefox'

tools = [
   {"name": "run_bash_command", "description": "Run shell/bash command in terminal.", "input_schema": {"type": "object", "properties": {"command": {"type": "string", "description": "Valid bash command to execute."}}, "required": ["command"]}},
   {"name": "start_virtual_os_sandbox", "description": "Start an isolated virtual Ubuntu OS environment (sandbox) and display it in the chat.", "input_schema": {"type": "object", "properties": {"vm_name": {"type": "string", "description": "Name of Virtual Machine to run.", "default": "UbuntuAIAgent"}}, "required": []}}
]

def get_claude_response(user_message):
    global sandbox_active
    
    intent = analyze_user_intent(user_message)
    auto_sandbox_triggered = False
    suggested_command = None
    
    if should_auto_start_sandbox(user_message) and intent['needs_desktop'] and not sandbox_active:
        print("AUTO-TRIGGERING SANDBOX...")
        start_virtual_os_sandbox("UbuntuAIAgent")
        auto_sandbox_triggered = True
        time.sleep(3)
    
    if intent['needs_desktop']:
        suggested_command = enhance_command_for_gui(user_message, intent)
    
    system_message = "You are an AI agent with computer use capabilities. You have access to bash commands and virtual desktop environment. For GUI applications, always use DISPLAY=:3 prefix. Be helpful and explain your actions."
    
    conversation = [
        {"role": "user", "content": f"{system_message}\n\nUser request: {user_message}"}
    ]
    
    while True:
        print("AI: Contacting Claude for next step...")
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620", 
                max_tokens=4096, 
                messages=conversation, 
                tools=tools, 
                tool_choice={"type": "auto"}
            )
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return "An error occurred while contacting AI."
        
        response_message = {"role": response.role, "content": response.content}
        conversation.append(response_message)
        
        if response.stop_reason == "tool_use":
            print("AI: Claude decided to use a tool.")
            tool_use = next((block for block in response.content if block.type == 'tool_use'), None)
            if not tool_use:
                return "An error occurred while trying to use tool."
            tool_name = tool_use.name
            tool_input = tool_use.input
            print(f"TOOLBOX: Calling tool '{tool_name}' with input: {tool_input}")
            try:
                if tool_name == "run_bash_command":
                    command_to_run = tool_input.get("command")
                    if suggested_command and intent['needs_desktop']:
                        command_to_run = suggested_command
                    tool_result = run_bash_command(command_to_run)
                elif tool_name == "start_virtual_os_sandbox":
                    if not auto_sandbox_triggered and not sandbox_active:
                        tool_result = start_virtual_os_sandbox(tool_input.get("vm_name", "UbuntuAIAgent"))
                    else:
                        tool_result = json.dumps({"status": "success", "message": "Sandbox already active"})
                else:
                    tool_result = f"Error: Tool '{tool_name}' not recognized."
            except Exception as e:
                tool_result = f"Error running tool {tool_name}: {str(e)}"
            conversation.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": tool_result}]})
        else:
            print("AI: Claude providing final answer.")
            final_text = next((block.text for block in response.content if block.type == 'text'), "I cannot provide a response at this time.")
            
            if auto_sandbox_triggered and intent['needs_desktop']:
                final_text = f"Desktop environment is now active. {final_text}"
            
            return final_text

@app.route('/')
def index():
   return "AI Agent Backend Running"

@socketio.on('connect')
def handle_connect():
   print('Connection: Client connected to server.')
   print(f'Connection origin: {request.environ.get("HTTP_ORIGIN")}')

@socketio.on('disconnect')
def handle_disconnect():
   print('Connection: Client disconnected from server.')

@socketio.on('user_message')
def handle_user_message(json_data):
   print(f'RAW MESSAGE RECEIVED: {json_data}')
   message = json_data.get('data', '')
   print(f"Connection: Received message from user: '{message}'")
   try:
       ai_response = get_claude_response(message)
       if ai_response:
           print(f"SENDING RESPONSE: {ai_response}")
           emit('agent_response', {'data': ai_response})
       else:
           emit('agent_response', {'data': "Sorry, an internal error occurred."})
   except Exception as e:
       print(f"Error handling message: {e}")
       emit('agent_response', {'data': "An error occurred while processing the message."})

if __name__ == '__main__':
   print("AI Agent 'Computer Use' server started.")
   print("Listening for connections at http://localhost:5000")
   socketio.run(app, host='0.0.0.0', port=5000)