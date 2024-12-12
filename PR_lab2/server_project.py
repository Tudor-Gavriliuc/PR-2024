import asyncio
import websockets
import psycopg2
import os
import http.server
import socketserver
import threading
from urllib.parse import urlparse, parse_qs

# Database configuration from environment variables
DATABASE_CONFIG = {
    "dbname": os.getenv("DATABASE_NAME", "testdb"),
    "user": os.getenv("DATABASE_USER", "user"),
    "password": os.getenv("DATABASE_PASSWORD", "password"),
    "host": os.getenv("DATABASE_HOST", "localhost"),
    "port": os.getenv("DATABASE_PORT", "5433"),
}

# Connect to the PostgreSQL database
conn = psycopg2.connect(**DATABASE_CONFIG)
cur = conn.cursor()

# Ensure the chat_messages table exists
cur.execute("""
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# WebSocket clients set
clients = set()

# WebSocket chat handler
async def chat_handler(websocket, path):
    clients.add(websocket)
    try:
        async for message in websocket:
            # Save the message in the database
            cur.execute("INSERT INTO chat_messages (message) VALUES (%s)", (message,))
            conn.commit()

            # Broadcast the message to all connected clients
            for client in clients:
                if client != websocket:
                    await client.send(message)
    except websockets.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        clients.remove(websocket)

# HTTP server for health checks or additional functionality
class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def _set_response(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/health':
            self._set_response()
            self.wfile.write(b'{"status": "OK"}')

if __name__ == "__main__":
    # Start WebSocket server
    print("Starting WebSocket server on ws://0.0.0.0:9090...")
    websocket_server = websockets.serve(chat_handler, "0.0.0.0", 9090)

    # Start HTTP server
    PORT = 8081
    print(f"Starting HTTP server on port {PORT}...")
    http_server = socketserver.TCPServer(("", PORT), RequestHandler)

    # Run WebSocket and HTTP servers concurrently
    loop = asyncio.get_event_loop()
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()

    try:
        loop.run_until_complete(websocket_server)
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        http_server.shutdown()
        conn.close()
