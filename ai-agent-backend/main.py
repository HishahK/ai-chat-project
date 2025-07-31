import os
import subprocess
import json
import re
import time
from flask import Flask
from flask_socketio import SocketIO, emit
import anthropic

app = Flask(__name__)
app.config['SECRET_KEY'] = 'computer-agent-secret-v3'
allowed_origins = [
   "https://ai-chat-project-ten.vercel.app",
   "https://e1094a65a1d1.ngrok-free.app"
]

socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
   print("Kesalahan: Environment variable ANTHROPIC_API_KEY tidak ditemukan.")
   print("Mohon jalankan: export ANTHROPIC_API_KEY='...' sebelum memulai.")
   exit()

client = anthropic.Anthropic(api_key=api_key)

def run_bash_command(command):
   print(f"TOOLBOX: Menjalankan perintah bash: {command}")
   try:
       result = subprocess.run(
           command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
       )
       return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
   except subprocess.CalledProcessError as e:
       return f"Kesalahan saat menjalankan perintah:\n{e.stderr}"

def open_website(url):
   print(f"TOOLBOX: Mengakses URL: {url}")
   command = f"curl -sL \"{url}\" | head -n 50"
   try:
       result = subprocess.run(
           command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
       )
       return f"Konten awal dari {url}:\n{result.stdout}"
   except subprocess.CalledProcessError as e:
       return f"Gagal mengakses URL {url}. Error:\n{e.stderr}"

def open_terminal_direct():
   print("TOOLBOX: Membuka terminal secara langsung")
   system = os.name
   try:
       if system == 'posix':
           terminals = [
               'gnome-terminal',
               'konsole', 
               'xterm',
               'mate-terminal',
               'xfce4-terminal',
               'terminator',
               'tilix',
               'alacritty',
               'kitty'
           ]
           
           for term in terminals:
               try:
                   subprocess.Popen([term], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  preexec_fn=os.setsid)
                   time.sleep(0.5)
                   return f"Terminal {term} berhasil dibuka"
               except (FileNotFoundError, OSError) as e:
                   print(f"Gagal membuka {term}: {e}")
                   continue
           
           try:
               subprocess.Popen(['x-terminal-emulator'], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL,
                              preexec_fn=os.setsid)
               time.sleep(0.5)
               return "Terminal default berhasil dibuka"
           except:
               pass
               
           return "Tidak dapat menemukan terminal di sistem"
           
       elif system == 'nt':
           try:
               subprocess.Popen(['cmd'], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL,
                              creationflags=subprocess.CREATE_NEW_CONSOLE)
               time.sleep(0.5)
               return "Command Prompt berhasil dibuka"
           except:
               try:
                   subprocess.Popen(['powershell'], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  creationflags=subprocess.CREATE_NEW_CONSOLE)
                   time.sleep(0.5)
                   return "PowerShell berhasil dibuka"
               except Exception as e:
                   return f"Gagal membuka terminal: {str(e)}"
                   
   except Exception as e:
       return f"Error membuka terminal: {str(e)}"

def open_multiple_terminals(count):
   print(f"TOOLBOX: Membuka {count} terminal")
   system = os.name
   opened_terminals = []
   
   try:
       if system == 'posix':
           terminals = ['gnome-terminal', 'konsole', 'xterm', 'mate-terminal', 'xfce4-terminal']
           
           working_terminal = None
           for term in terminals:
               try:
                   subprocess.Popen([term], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  preexec_fn=os.setsid)
                   working_terminal = term
                   break
               except FileNotFoundError:
                   continue
           
           if not working_terminal:
               return "Tidak dapat menemukan terminal yang bisa dibuka"
           
           for i in range(count):
               try:
                   subprocess.Popen([working_terminal], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  preexec_fn=os.setsid)
                   opened_terminals.append(f"Terminal {i+1}")
                   time.sleep(0.3)
               except Exception as e:
                   print(f"Error membuka terminal {i+1}: {e}")
                   continue
                   
       elif system == 'nt':
           for i in range(count):
               try:
                   subprocess.Popen(['cmd'], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  creationflags=subprocess.CREATE_NEW_CONSOLE)
                   opened_terminals.append(f"CMD {i+1}")
                   time.sleep(0.3)
               except Exception as e:
                   print(f"Error membuka CMD {i+1}: {e}")
                   continue
       
       if opened_terminals:
           return f"Berhasil membuka {len(opened_terminals)} terminal: {', '.join(opened_terminals)}"
       else:
           return "Gagal membuka terminal"
           
   except Exception as e:
       return f"Error: {str(e)}"

def open_terminal_with_command(command):
   print(f"TOOLBOX: Membuka terminal dengan command: {command}")
   system = os.name
   try:
       if system == 'posix':
           terminals_with_command = [
               ['gnome-terminal', '--', 'bash', '-c', f'{command}; exec bash'],
               ['konsole', '-e', 'bash', '-c', f'{command}; exec bash'],
               ['xterm', '-e', 'bash', '-c', f'{command}; exec bash'],
               ['mate-terminal', '-e', f'bash -c "{command}; exec bash"'],
               ['xfce4-terminal', '-e', f'bash -c "{command}; exec bash"']
           ]
           
           for term_cmd in terminals_with_command:
               try:
                   subprocess.Popen(term_cmd, 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  preexec_fn=os.setsid)
                   time.sleep(0.5)
                   return f"Terminal dibuka dengan command: {command}"
               except (FileNotFoundError, OSError):
                   continue
                   
           return "Tidak dapat membuka terminal dengan command"
           
       elif system == 'nt':
           try:
               subprocess.Popen(['cmd', '/k', command], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL,
                              creationflags=subprocess.CREATE_NEW_CONSOLE)
               time.sleep(0.5)
               return f"Command Prompt dibuka dengan: {command}"
           except Exception as e:
               return f"Gagal membuka terminal dengan command: {str(e)}"
               
   except Exception as e:
       return f"Error: {str(e)}"

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
       "name": "open_website",
       "description": "Mengakses URL yang diberikan dan mengembalikan konten awal dari halaman web tersebut.",
       "input_schema": {
           "type": "object",
           "properties": {"url": {"type": "string", "description": "URL lengkap dari situs yang akan diakses"}},
           "required": ["url"],
       },
   },
   {
       "name": "open_terminal_direct",
       "description": "Membuka aplikasi terminal baru secara langsung. Gunakan ketika user meminta 'open terminal', 'buka terminal', atau sejenisnya.",
       "input_schema": {
           "type": "object",
           "properties": {},
           "required": [],
       },
   },
   {
       "name": "open_multiple_terminals",
       "description": "Membuka beberapa terminal sekaligus. Gunakan ketika user meminta membuka lebih dari 1 terminal.",
       "input_schema": {
           "type": "object",
           "properties": {"count": {"type": "integer", "description": "Jumlah terminal yang akan dibuka"}},
           "required": ["count"],
       },
   },
   {
       "name": "open_terminal_with_command",
       "description": "Membuka terminal baru dan langsung menjalankan command tertentu di dalamnya.",
       "input_schema": {
           "type": "object",
           "properties": {"command": {"type": "string", "description": "Command yang akan dijalankan di terminal baru"}},
           "required": ["command"],
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
           
           tool_result = ""
           try:
               if tool_name == "run_bash_command":
                   tool_result = run_bash_command(tool_input.get("command"))
               elif tool_name == "open_website":
                   tool_result = open_website(tool_input.get("url"))
               elif tool_name == "open_terminal_direct":
                   tool_result = open_terminal_direct()
               elif tool_name == "open_multiple_terminals":
                   count = tool_input.get("count", 1)
                   if count > 10:
                       count = 10
                   tool_result = open_multiple_terminals(count)
               elif tool_name == "open_terminal_with_command":
                   tool_result = open_terminal_with_command(tool_input.get("command"))
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
           return next((block.text for block in response.content if block.type == 'text'), "Saya tidak bisa memberikan respons saat ini.")

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