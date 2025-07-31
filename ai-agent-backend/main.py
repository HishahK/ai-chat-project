import os
import subprocess
import json
import re
import time
from flask import Flask
from flask_socketio import SocketIO, emit
import anthropic
from pyngrok import ngrok

app = Flask(__name__)
app.config['SECRET_KEY'] = 'computer-agent-secret-v3'
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Kesalahan: Environment variable ANTHROPIC_API_KEY tidak ditemukan.")
    print("Mohon jalankan: export ANTHROPIC_API_KEY='...' sebelum memulai.")
    exit()
client = anthropic.Anthropic(api_key=api_key)

VBOX_MANAGE_PATH = "C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe" if os.name == 'nt' else "VBoxManage"

def run_bash_command(command):
    print(f"TOOLBOX: Menjalankan perintah bash: {command}")
    try:
        result = subprocess.run(
            command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30
        )
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        return f"Kesalahan saat menjalankan perintah:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
    except subprocess.TimeoutExpired:
        return "Kesalahan: Waktu eksekusi perintah habis (30 detik)."

def start_virtual_os_sandbox(vm_name="AI-Server-VM"):
    print(f"TOOLBOX: Memulai sandbox untuk VM: {vm_name}")
    HOST_PORT_VNC = 6080

    try:
        print(f"Mengecek status VM '{vm_name}'...")
        info_result = subprocess.run([VBOX_MANAGE_PATH, "showvminfo", vm_name], capture_output=True, text=True)
        if "running (since" not in info_result.stdout:
            print(f"VM tidak berjalan. Memulai VM '{vm_name}' secara headless...")
            subprocess.run([VBOX_MANAGE_PATH, "startvm", vm_name, "--type", "headless"], check=True)
            time.sleep(15)
        else:
            print(f"VM '{vm_name}' sudah berjalan.")

        for tunnel in ngrok.get_tunnels():
            if tunnel.config['addr'].endswith(str(HOST_PORT_VNC)):
                print(f"Menutup tunnel ngrok yang sudah ada: {tunnel.public_url}")
                ngrok.disconnect(tunnel.public_url)

        print(f"Membuka tunnel ngrok ke http://localhost:{HOST_PORT_VNC}...")
        tunnel = ngrok.connect(HOST_PORT_VNC, "http")
        public_url = tunnel.public_url
        print(f"Tunnel ngrok berhasil dibuat: {public_url}")

        vnc_view_url = f"{public_url}/vnc.html?host={tunnel.public_url.split('//')[1]}&port=443&path=websockify"
        
        return json.dumps({
            "status": "success",
            "message": f"Sandbox untuk {vm_name} berhasil dimulai.",
            "vnc_view_url": vnc_view_url
        })

    except FileNotFoundError:
        return json.dumps({"status": "error", "message": f"Perintah VBoxManage tidak ditemukan di '{VBOX_MANAGE_PATH}'. Mohon periksa path."})
    except subprocess.CalledProcessError as e:
        return json.dumps({"status": "error", "message": f"Gagal menjalankan perintah VirtualBox: {e.stderr}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Terjadi kesalahan tak terduga: {str(e)}"})

tools = [
    {
        "name": "run_bash_command",
        "description": "Menjalankan perintah shell/bash di terminal. Berguna untuk navigasi file (ls, pwd), membaca file (cat), dll.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Perintah bash yang valid untuk dijalankan."}},
            "required": ["command"],
        },
    },
    {
        "name": "start_virtual_os_sandbox",
        "description": "Memulai lingkungan OS Ubuntu virtual yang terisolasi (sandbox) dan menampilkannya di dalam chat. Gunakan tool ini ketika pengguna meminta untuk 'menjalankan OS virtual', 'membuka sandbox ubuntu', atau permintaan sejenisnya.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vm_name": {
                    "type": "string",
                    "description": "Nama Virtual Machine yang akan dijalankan. Defaultnya adalah 'AI-Server-VM'.",
                    "default": "AI-Server-VM"
                }
            },
            "required": [],
        },
    }
]

def get_claude_response(user_message):
    conversation = [{"role": "user", "content": user_message}]

    while True:
        print("AI: Menghubungi Claude untuk langkah berikutnya...")
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
            return "Terjadi kesalahan saat menghubungi AI."

        response_message = {"role": response.role, "content": response.content}
        conversation.append(response_message)

        if response.stop_reason == "tool_use":
            print("AI: Claude memutuskan untuk menggunakan sebuah tool.")
            tool_use = next((block for block in response.content if block.type == 'tool_use'), None)
            
            if not tool_use:
                return "Terjadi kesalahan saat mencoba menggunakan tool."

            tool_name = tool_use.name
            tool_input = tool_use.input
            
            print(f"TOOLBOX: Memanggil tool '{tool_name}' dengan input: {tool_input}")
            
            tool_result = ""
            try:
                if tool_name == "run_bash_command":
                    tool_result = run_bash_command(tool_input.get("command"))
                elif tool_name == "start_virtual_os_sandbox":
                    tool_result = start_virtual_os_sandbox(tool_input.get("vm_name", "AI-Server-VM"))
                else:
                    tool_result = f"Kesalahan: Tool '{tool_name}' tidak dikenal."
            except Exception as e:
                tool_result = f"Error menjalankan tool {tool_name}: {str(e)}"
            
            conversation.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": tool_result}]
            })
        else:
            print("AI: Claude memberikan jawaban akhir.")
            final_text = next((block.text for block in response.content if block.type == 'text'), "Saya tidak bisa memberikan respons saat ini.")
            return final_text

@socketio.on('connect')
def handle_connect():
    print('Koneksi: Client terhubung ke server.')

@socketio.on('disconnect')
def handle_disconnect():
    print('Koneksi: Client terputus dari server.')

@socketio.on('user_message')
def handle_user_message(json_data):
    message = json_data.get('data', '')
    print(f"Koneksi: Menerima pesan dari user: '{message}'")
    try:
        ai_response = get_claude_response(message)
        if ai_response:
            emit('agent_response', {'data': ai_response})
        else:
            emit('agent_response', {'data': "Maaf, terjadi kesalahan internal."})
    except Exception as e:
        print(f"Error handling message: {e}")
        emit('agent_response', {'data': "Terjadi kesalahan saat memproses pesan."})

if __name__ == '__main__':
    print("Server AI Agent 'Computer Use' telah dimulai.")
    print("Mendengarkan koneksi di http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
