import http.server
import json
import os
import sqlite3

import base64
import hashlib
import socketserver
import threading

from urllib.parse import urlparse, parse_qs

# Configuration
DATABASE = 'data.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set up SQLite database
conn = sqlite3.connect(DATABASE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    data TEXT NOT NULL
)
""")
conn.commit()

# HTTP Request Handler
class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def _set_response(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/resources':
            query_params = parse_qs(parsed_path.query)
            offset = int(query_params.get('offset', [0])[0])
            limit = int(query_params.get('limit', [10])[0])
            cursor.execute("SELECT * FROM resources LIMIT ? OFFSET ?", (limit, offset))
            resources = cursor.fetchall()
            self._set_response()
            self.wfile.write(json.dumps(
                [{"id": r[0], "name": r[1], "data": r[2]} for r in resources]
            ).encode('utf-8'))

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/resources':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            cursor.execute("INSERT INTO resources (name, data) VALUES (?, ?)",
                           (post_data['name'], post_data['data']))
            conn.commit()
            self._set_response(201)
            self.wfile.write(json.dumps({"message": "Resource created"}).encode('utf-8'))

        elif parsed_path.path == '/upload':
            content_type = self.headers['Content-Type']
            if 'multipart/form-data' in content_type:
                boundary = content_type.split("boundary=")[-1]
                post_data = self.rfile.read(int(self.headers['Content-Length']))
                parts = post_data.split(b"--" + boundary.encode() + b"\r\n")
                for part in parts:
                    if b'filename="' in part:
                        filename = part.split(b'filename="')[1].split(b'"')[0].decode()
                        file_content = part.split(b'\r\n\r\n')[1].split(b'\r\n--')[0]
                        with open(os.path.join(UPLOAD_FOLDER, filename), 'wb') as f:
                            f.write(file_content)
                        with open(os.path.join(UPLOAD_FOLDER, filename), 'r') as f:
                            json_content = json.load(f)
                        self._set_response()
                        self.wfile.write(json.dumps({"message": "File uploaded successfully", "content": json_content}).encode('utf-8'))

    def do_PUT(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/resources/'):
            resource_id = int(parsed_path.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            put_data = json.loads(self.rfile.read(content_length))
            cursor.execute("UPDATE resources SET name = ?, data = ? WHERE id = ?",
                           (put_data.get('name'), put_data.get('data'), resource_id))
            conn.commit()
            self._set_response()
            self.wfile.write(json.dumps({"message": "Resource updated"}).encode('utf-8'))

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith('/resources/'):
            resource_id = int(parsed_path.path.split('/')[-1])
            cursor.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
            conn.commit()
            self._set_response()
            self.wfile.write(json.dumps({"message": "Resource deleted"}).encode('utf-8'))

# WebSocket Server for Chat Room
class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, host, port):
        super().__init__((host, port), self.ChatHandler)
        self.clients = []

    class ChatHandler(socketserver.BaseRequestHandler):
        def handle(self):
            # Perform WebSocket handshake
            headers = self.request.recv(1024).decode().split("\r\n")
            websocket_key = None

            for header in headers:
                if header.startswith("Sec-WebSocket-Key:"):
                    websocket_key = header.split(":")[1].strip()

            if websocket_key:
                accept_key = base64.b64encode(
                    hashlib.sha1((websocket_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
                ).decode()
                handshake_response = (
                    "HTTP/1.1 101 Switching Protocols\r\n"
                    "Upgrade: websocket\r\n"
                    "Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
                )
                self.request.sendall(handshake_response.encode())

                # Add client to the list
                self.server.clients.append(self.request)
                print(f"New client connected: {self.client_address}")

                try:
                    while True:
                        # Read a WebSocket frame
                        message = self._receive_frame()
                        if not message:
                            break
                        print(f"Received message from {self.client_address}: {message}")
                        # Broadcast the message to other clients
                        for client in self.server.clients:
                            if client is not self.request:
                                self._send_frame(client, message)
                except Exception as e:
                    print(f"Error: {e}")
                finally:
                    print(f"Client disconnected: {self.client_address}")
                    self.server.clients.remove(self.request)

        def _receive_frame(self):
            # Read the first 2 bytes of the frame
            frame_header = self.request.recv(2)
            if not frame_header:
                return None

            # Parse the header
            byte1, byte2 = frame_header
            fin = byte1 >> 7
            opcode = byte1 & 0x0F
            masked = byte2 >> 7
            payload_length = byte2 & 0x7F

            if opcode == 0x8:  # Close frame
                return None

            # Read extended payload length if needed
            if payload_length == 126:
                payload_length = struct.unpack(">H", self.request.recv(2))[0]
            elif payload_length == 127:
                payload_length = struct.unpack(">Q", self.request.recv(8))[0]

            # Read the masking key if present
            if masked:
                masking_key = self.request.recv(4)
                payload = bytearray(self.request.recv(payload_length))
                for i in range(payload_length):
                    payload[i] ^= masking_key[i % 4]
            else:
                payload = self.request.recv(payload_length)

            return payload.decode("utf-8")

        def _send_frame(self, client, message):
            # Build a WebSocket frame
            payload = message.encode("utf-8")
            frame = bytearray()
            frame.append(0x81)  # FIN and text frame
            payload_length = len(payload)

            if payload_length <= 125:
                frame.append(payload_length)
            elif payload_length <= 65535:
                frame.append(126)
                frame.extend(struct.pack(">H", payload_length))
            else:
                frame.append(127)
                frame.extend(struct.pack(">Q", payload_length))

            frame.extend(payload)
            client.sendall(frame)

    def run(self):
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()

# Start the servers
if __name__ == '__main__':
    PORT = 8081  # Updated port
    CHAT_PORT = 9090

    print(f"Starting HTTP server on port {PORT}...")
    http_server = socketserver.TCPServer(('', PORT), RequestHandler)

    print(f"Starting Chat server on port {CHAT_PORT}...")
    chat_server = ChatServer('0.0.0.0', CHAT_PORT)
    chat_server.run()

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        http_server.shutdown()
        conn.close()