import os
import subprocess
import json
from flask import Flask
from flask_socketio import SocketIO, emit
import anthropic

# Inisialisasi server web Flask dan koneksi real-time SocketIO.
app = Flask(__name__)
app.config['SECRET_KEY'] = 'computer-agent-secret-v3'
socketio = SocketIO(app, cors_allowed_origins="*")

# Mengambil API key dari environment variable untuk keamanan.
# Script akan berhenti jika API key tidak ditemukan.
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Kesalahan: Environment variable ANTHROPIC_API_KEY tidak ditemukan.")
    print("Mohon jalankan: export ANTHROPIC_API_KEY='...' sebelum memulai.")
    exit()

# Membuat klien untuk berkomunikasi dengan API Anthropic.
client = anthropic.Anthropic(api_key=api_key)


# Implementasi untuk tool yang bisa menjalankan perintah bash.
def run_bash_command(command):
    """Menjalankan perintah shell/bash di terminal dan mengembalikan outputnya."""
    print(f"TOOLBOX: Menjalankan perintah bash: {command}")
    try:
        result = subprocess.run(
            command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        return f"Kesalahan saat menjalankan perintah:\n{e.stderr}"

# Implementasi untuk tool yang bisa "membuka" website menggunakan curl.
def open_website(url):
    """Menggunakan curl untuk mengambil 50 baris pertama dari konten URL."""
    print(f"TOOLBOX: Mengakses URL: {url}")
    command = f"curl -sL \"{url}\" | head -n 50"
    try:
        result = subprocess.run(
            command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return f"Konten awal dari {url}:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Gagal mengakses URL {url}. Error:\n{e.stderr}"

# Skema atau "menu" dari semua kemampuan yang tersedia untuk AI.
# AI membaca deskripsi ini untuk memutuskan kapan harus menggunakan sebuah tool.
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
        "description": "Mengakses URL yang diberikan dan mengembalikan konten awal dari halaman web tersebut. Gunakan ini untuk memeriksa isi sebuah situs.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL lengkap dari situs yang akan diakses, contoh: 'https://www.google.com'"}},
            "required": ["url"],
        },
    }
]


def get_claude_response(user_message):
    """Mengelola siklus percakapan dengan Claude, termasuk penggunaan tool."""
    conversation = [{"role": "user", "content": user_message}]

    while True:
        print("AI: Menghubungi Claude untuk langkah berikutnya...")
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            messages=conversation,
            tools=tools,
        )

        # Menambahkan respons dari AI ke dalam riwayat percakapan.
        # Ini penting untuk menjaga konteks yang benar saat menggunakan tool.
        response_message = {"role": response.role, "content": response.content}
        conversation.append(response_message)

        if response.stop_reason == "tool_use":
            print("AI: Claude memutuskan untuk menggunakan sebuah tool.")
            tool_use = next((block for block in response.content if block.type == 'tool_use'), None)
            
            if not tool_use:
                return "Terjadi kesalahan saat mencoba menggunakan tool."

            tool_name = tool_use.name
            tool_input = tool_use.input
            
            # Memilih dan menjalankan tool yang sesuai.
            tool_result = ""
            if tool_name == "run_bash_command":
                tool_result = run_bash_command(tool_input.get("command"))
            elif tool_name == "open_website":
                tool_result = open_website(tool_input.get("url"))
            else:
                tool_result = f"Kesalahan: Tool '{tool_name}' tidak dikenal."
            
            # Menambahkan hasil dari tool ke dalam riwayat percakapan.
            conversation.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": tool_result}]
            })
        else:
            # Jika AI tidak menggunakan tool, berarti ini adalah jawaban akhir.
            print("AI: Claude memberikan jawaban akhir.")
            return next((block.text for block in response.content if block.type == 'text'), "Saya tidak bisa memberikan respons saat ini.")


@socketio.on('connect')
def handle_connect():
    """Dipanggil saat client (browser) berhasil terhubung."""
    print('Koneksi: Client terhubung ke server.')

@socketio.on('disconnect')
def handle_disconnect():
    """Dipanggil saat client (browser) terputus."""
    print('Koneksi: Client terputus dari server.')

@socketio.on('user_message')
def handle_user_message(json_data):
    """Menerima pesan dari browser, memprosesnya, dan mengirim kembali jawaban AI."""
    message = json_data.get('data', '')
    print(f"Koneksi: Menerima pesan dari user: '{message}'")
    ai_response = get_claude_response(message)
    if ai_response:
        emit('agent_response', {'data': ai_response})
    else:
        emit('agent_response', {'data': "Maaf, terjadi kesalahan internal."})


# Titik masuk utama untuk menjalankan server aplikasi.
if __name__ == '__main__':
    print("Server AI Agent 'Computer Use' telah dimulai.")
    print("Mendengarkan koneksi di http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)

