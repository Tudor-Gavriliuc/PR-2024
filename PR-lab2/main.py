from datetime import datetime
import threading
from db_operations import get_all_cars, get_car_by_id, get_paginated_cars, insert_car, create_cars_table, insert_multiple_cars, update_car
import json
import socket
from router_functions import delete_car, formatting_cars_json, car_in_dict, parse_multipart_form_data, post_car, take_raw_json, take_updated_fields
from urllib.parse import unquote
import asyncio
import json
from websockets import WebSocketServerProtocol, serve
from pprint import pprint

bad_request = 400
ok_request = 200


create_cars_table()
chat_rooms = {}

def load_cars_from_json(filename):
    """Loads car data from a JSON file and formats it for insertion."""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        car_list = []
        for car in data['cars']:
            # Convert updateDate to a datetime object
            update_date = datetime.strptime(car['updateDate'], "%A, %B %d, %Y at %I:%M %p")
            car_list.append((
                car['name'],
                car['price'],
                car['currency'],
                car['km'] if car['km'] != "None" else None,
                car['url'],
                update_date,
                car['type'],
                int(car['views'])
            ))
        return car_list
    
cars_list = load_cars_from_json('cars.json')

insert_multiple_cars(cars_list)

def parse_request(request_data):
    try:
        request_line = request_data.splitlines()[0]
        method, path, _ = request_line.split()
        print(f"Method: {method}, Path: {path}")
        segments_route = path.split('/')[1:]  # Split the path into segments
        query_params = {}
        
        # Check for query parameters in the path
        if '?' in segments_route[-1]:
            segments_route[-1], query_string = segments_route[-1].split('?')
            for param in query_string.split('&'):
                key, value = param.split('=')
                query_params[unquote(key)] = unquote(value)
        
        print(f"Segments: {segments_route}, Query Params: {query_params}")
        return method, segments_route, query_params
    except Exception as e:
        print(f"Error parsing request: {e}")
        return None, None, None

def routing(method, routes, params, request_data):
    route = "/".join(routes)
    if method == "GET" and route == "hello":
        return ok_request, "Hello World"
    elif method == "GET" and route == "":
        if params.get('id') is None:
            cars = get_all_cars()
            return ok_request,json.dumps(formatting_cars_json(cars), default=str)
        
        car = get_car_by_id(params["id"])
        if len(car) == 0:
            return bad_request, "No such ID"
        return ok_request, json.dumps(formatting_cars_json(car), default=str)
    
    elif method == "PUT" and route == "":
        if params.get('id') is None:
            return bad_request, "ID is not Provided"
        
        fields, values = take_updated_fields(params['id'], params)
        
        if not fields:
            return bad_request, "No valid fields provided for update"
        
        response_status, response_body = update_car(fields, values)
        print(response_body)
        return response_status, response_body
    
    elif method == "POST" and route == "":
        response_status, response_body = post_car(params)
        return response_status, response_body
    
    elif method == "DELETE" and route == "":
        if params.get('id') is None:
            return bad_request, "ID is not Provided"
        response_status, response_body = delete_car(params["id"])
        return response_status, response_body

    elif method == "GET" and route == "pagination":
        page = 1
        size = 5
        if params.get('page') is not None:
            try:
                page = int(params['page'])
                if page < 1:
                    return bad_request, "Page must be > 1"
            except ValueError:
                return bad_request, "Page must be integer"
        if params.get('size') is not None:
            try:
                size = int(params['size'])
                if size < 1:
                    return bad_request, "Size must be > 1"
            except ValueError:
                return bad_request, "Size must be integer"
        
        cars = get_paginated_cars(page, size)
        
        if not cars:
            return ok_request, json.dumps([])
        
        return ok_request, json.dumps(formatting_cars_json(cars), default=str)
    
    elif method == "GET" and route == "join":
        return ok_request, json.dumps("Join a chat room by connecting via WebSocket", default=str)
    
    elif method == "GET" and route == "rooms":
        room_list = list(chat_rooms.keys())
        return ok_request, json.dumps(f"'rooms': {room_list}", default=str)
    
    elif method == "POST" and route == "create_room":
        result = take_raw_json(request_data)
        room_name = result['room']
        if chat_rooms.get(room_name) is not None:
            return bad_request, json.dumps({"message": f"Room '{room_name}' already created"}, default=str)
        chat_rooms[room_name] = []
        return ok_request, json.dumps({"message": f"Room '{room_name}' created"}, default=str)
    
    
    elif method == "POST" and route == "json":
        print("-------------------------JSON FORM DATA---------------------------------")
        form_data = parse_multipart_form_data(request_data)
        for data in form_data:
            pprint(data)
        return 200, json.dumps(form_data, default=str)
    else:
        return None, None

def run_server(host='0.0.0.0', port=8080):
    # Create a socket that uses IPv4 and TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server is listening on {host}:{port}")
    while True:
        # Accept incoming client connections
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

        request_data = b"" # Empty byte string
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            request_data += data
            if b'multipart/form-data' not in request_data:
                break
            print(data)
            if b'--\r\n' in data:
                break
        
        request_data = request_data.decode('utf-8')
        print(f"Received Request:\n{request_data}")

        method, segments_route, query_params = parse_request(request_data)

        if segments_route != None and segments_route[0] != 'favicon.ico':
            status, response_body = routing(method, segments_route, query_params, request_data)
            
            if response_body is None:
                response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\n404 Not Found"
            else:
                response = f"HTTP/1.1 {status} OK\r\nContent-Type: application/json\r\n\r\n" + response_body
        else:
            response = "HTTP/1.1 204 No Content\r\n\r\n" # Handle favicon
        
        # Send the HTTP response back to the client
        client_socket.sendall(response.encode('utf-8'))

        # Close the client socket
        client_socket.close()

# WebSocket Server Handler
async def chat_handler(websocket: WebSocketServerProtocol, path):
    room_name = None

    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")

            if action == "join":
                room_name = data.get("room")
                if room_name in chat_rooms:
                    chat_rooms[room_name].append(websocket)
                    await websocket.send(json.dumps({"message": f"Joined room '{room_name}'"}))
                    print(f"User joined room {room_name}")
                else:
                    room_name = None
                    await websocket.send(json.dumps({"message": "Room does not exist"}))
            
            elif action == "create" and not room_name:
                new_room = data.get('room')
                if chat_rooms.get(new_room) is not None:
                    return await websocket.send(json.dumps({"message": f"Room '{new_room}' already created"}, default=str))
                chat_rooms[new_room] = []
                await websocket.send(json.dumps({"message": f"Room '{new_room}' created"}, default=str))
            
            elif action == "rooms":
                room_list = list(chat_rooms.keys())
                await websocket.send(json.dumps({"rooms": room_list}))
                    
            elif action == "message" and room_name:
                message_text = data.get("message")
                if message_text:
                    await broadcast(room_name, message_text, websocket)

            elif action == "leave" and room_name:
                await leave_room(room_name, websocket)
                room_name = None
                await websocket.send(json.dumps({"message": "Left the room"}))

    finally:
        if room_name:
            await leave_room(room_name, websocket)

async def broadcast(room, message, sender):
    #Broadcast a message to all users in the room except the sender
    if room in chat_rooms:
        message_data = json.dumps({"message": message})
        for user in chat_rooms[room]:
            if user != sender:
                await user.send(message_data)

async def leave_room(room, websocket):
    if room in chat_rooms:
        chat_rooms[room].remove(websocket)
        print(f"User left room {room}")

# Run WebSocket Server in Thread
def start_websocket_server(port=8090):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(serve(chat_handler, "0.0.0.0", port))
    loop.run_forever()


http_thread = threading.Thread(target=run_server)
http_thread.start()
websocket_thread = threading.Thread(target=start_websocket_server)
websocket_thread.start()

websocket_thread.join()
http_thread.join()

# Example data
# name = "Mercedes GLE Coupe, 2016 an"
# price = 944000
# currency = "MDL"
# km = "135 km"
# url = "https://999.md/ro/88473766"
# update_date = datetime(2024, 10, 10, 15, 37)
# type = "Vând"
# views = 26

# # Insert car data
# insert_car(name, price, currency, km, url, update_date, type, views)
