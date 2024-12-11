import http.server
import json
import os
import sqlite3
import socketserver
import threading
from urllib.parse import urlparse, parse_qs

DATABASE = 'data.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

file_condition = threading.Condition()
shared_file = "shared.txt"

def write_to_shared_file(data):
    with file_condition:
        with open(shared_file, "a") as f:
            f.write(data + "\n")
        file_condition.notify_all()

def read_from_shared_file():
    with file_condition:
        file_condition.wait()
        with open(shared_file, "r") as f:
            return f.read()

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

class FileTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class FileTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(1024).decode().strip()
            command, *args = data.split(" ", 1)

            if command == "WRITE":
                if args:
                    write_to_shared_file(args[0])
                    self.request.sendall(b"WRITE OK")
                else:
                    self.request.sendall(b"ERROR: Missing data for WRITE")

            elif command == "READ":
                file_content = read_from_shared_file()
                self.request.sendall(file_content.encode())

            else:
                self.request.sendall(b"ERROR: Unknown command")
        except Exception as e:
            self.request.sendall(f"ERROR: {e}".encode())

if __name__ == '__main__':
    PORT = 8081
    TCP_PORT = 9091

    print(f"Starting HTTP server on port {PORT}...")
    http_server = socketserver.TCPServer(('', PORT), RequestHandler)

    print(f"Starting TCP server on port {TCP_PORT}...")
    tcp_server = FileTCPServer(('0.0.0.0', TCP_PORT), FileTCPHandler)

    tcp_thread = threading.Thread(target=tcp_server.serve_forever)
    tcp_thread.daemon = True
    tcp_thread.start()

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        http_server.shutdown()
        tcp_server.shutdown()
        conn.close()
