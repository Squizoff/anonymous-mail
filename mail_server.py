import socket
import json
import sqlite3
import os
import secrets
import random
import time

HOST = 'localhost'
PORT = 55555
MAX_REQUESTS_PER_IP = 5

conn = sqlite3.connect('mail.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        key_file TEXT NOT NULL,
        key TEXT NOT NULL,
        email TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL
    )
''')

conn.commit()

DOMAINS = ['ntwrkhole', 'networkhole', 'inhole', 'nethole']

ip_last_request_time = {}

def register_user():
    username = secrets.token_urlsafe(15)
    key = secrets.token_urlsafe(random.randint(1000, 100000))
    key_file = f"{username}.key"
    domain = random.choice(DOMAINS)
    email = f"{username}@{domain}.anon"

    cursor.execute('INSERT INTO users (username, key_file, key, email) VALUES (?, ?, ?, ?)', (username, key_file, key, email))
    conn.commit()

    with open(key_file, 'w') as f:
        f.write(key)

    return {'success': True, 'message': f"Registration successful. Your email: {email}, save your key file {key_file}"}

def login_user(key_file_path):
    if os.path.exists(key_file_path):
        with open(key_file_path, 'r') as f:
            key = f.read().strip()

        cursor.execute('SELECT * FROM users WHERE key_file = ?', (os.path.basename(key_file_path),))
        user = cursor.fetchone()

        if user:
            stored_key = user[3]
            if key == stored_key:
                return {'success': True, 'message': f"Login successful. Your email: {user[4]}"}
            else:
                return {'success': False, 'message': "Invalid key."}
        else:
            return {'success': False, 'message': "User with the specified key file not found."}
    else:
        return {'success': False, 'message': "The specified key file does not exist."}

def send_email(sender_email, recipient, subject, body):
    cursor.execute('INSERT INTO emails (sender, recipient, subject, body) VALUES (?, ?, ?, ?)',
                   (sender_email, recipient, subject, body))
    conn.commit()

    return {'success': True, 'message': "Email sent successfully."}

def get_emails(recipient_email):
    cursor.execute('SELECT * FROM emails WHERE recipient = ?', (recipient_email,))
    emails = cursor.fetchall()

    return emails

def handle_request(request, client_socket):
    global ip_last_request_time

    client_ip = client_socket.getpeername()[0]

    current_time = time.time()
    if client_ip in ip_last_request_time:
        last_request_time = ip_last_request_time[client_ip]
        if current_time - last_request_time < 10:
            response = {'success': False, 'message': 'Too many requests. Please try again later.'}
            client_socket.send(json.dumps(response).encode('utf-8'))
            return

    ip_last_request_time[client_ip] = current_time

    try:
        request_data = json.loads(request)
    except json.JSONDecodeError:
        response = {'success': False, 'message': 'Invalid JSON format.'}
        client_socket.send(json.dumps(response).encode('utf-8'))
        return

    action = request_data.get('action')

    if action == 'REGISTER':
        response_data = register_user()

    elif action == 'LOGIN':
        key_file_path = request_data.get('key_file_path')
        response_data = login_user(key_file_path)

    elif action == 'SEND':
        sender_email = request_data.get('sender_email')
        recipient = request_data.get('recipient')
        subject = request_data.get('subject')
        body = request_data.get('body')
        response_data = send_email(sender_email, recipient, subject, body)

    elif action == 'RETRIEVE':
        recipient_email = request_data.get('recipient_email')
        response_data = get_emails(recipient_email)
        if not response_data:
            response_data = []

    else:
        response_data = {'success': False, 'message': 'Invalid action.'}

    client_socket.send(json.dumps(response_data).encode('utf-8'))

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)

        print(f"Server running on {HOST}:{PORT}...")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr}")

            request = client_socket.recv(1024).decode('utf-8')

            if not request:
                continue

            handle_request(request, client_socket)

            client_socket.close()

if __name__ == "__main__":
    main()