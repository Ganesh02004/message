import network
import socket
import json
import time
import hashlib
from machine import Pin

# WiFi Configuration
SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

# Global data structures
chat_rooms = {}  # {room_name: {'key': str, 'users': {}, 'messages': []}}
active_connections = {}  # {conn_id: {'conn': socket, 'name': str, 'room': str}}
conn_counter = 0

# LED for status (optional)
led = Pin(2, Pin.OUT)

def connect_wifi():
    """Connect to WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(SSID, PASSWORD)
        
        timeout = 0
        while not wlan.isconnected() and timeout < 20:
            led.value(not led.value())
            time.sleep(0.5)
            timeout += 1
    
    if wlan.isconnected():
        led.value(1)
        print('WiFi Connected!')
        print('IP Address:', wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    else:
        print('WiFi Connection Failed')
        return None

def parse_http_request(data):
    """Parse HTTP request"""
    try:
        lines = data.decode('utf-8').split('\r\n')
        request_line = lines[0].split(' ')
        method = request_line[0]
        path = request_line[1]
        
        headers = {}
        body = ""
        body_start = False
        
        for line in lines[1:]:
            if line == "":
                body_start = True
                continue
            if body_start:
                body += line
            else:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
        
        return method, path, headers, body
    except:
        return None, None, None, None

def create_response(status, content_type, body, cors=True):
    """Create HTTP response"""
    response = f"HTTP/1.1 {status}\r\n"
    if cors:
        response += "Access-Control-Allow-Origin: *\r\n"
        response += "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        response += "Access-Control-Allow-Headers: Content-Type\r\n"
    response += f"Content-Type: {content_type}\r\n"
    response += f"Content-Length: {len(body)}\r\n"
    response += "Connection: close\r\n"
    response += "\r\n"
    response += body
    return response

def handle_get_rooms():
    """Get list of rooms"""
    rooms = []
    for room_name, room_data in chat_rooms.items():
        rooms.append({
            'name': room_name,
            'user_count': len(room_data['users'])
        })
    
    return json.dumps({'rooms': rooms})

def handle_create_room(body):
    """Create a new room"""
    try:
        data = json.loads(body)
        room_name = data.get('room_name')
        room_key = data.get('room_key', '')
        
        if not room_name:
            return json.dumps({'error': 'Room name required'}), '400 Bad Request'
        
        if room_name in chat_rooms:
            return json.dumps({'error': 'Room already exists'}), '400 Bad Request'
        
        chat_rooms[room_name] = {
            'key': room_key,
            'users': {},
            'messages': []
        }
        
        return json.dumps({
            'success': True,
            'message': f'Room "{room_name}" created'
        }), '200 OK'
    except:
        return json.dumps({'error': 'Invalid request'}), '400 Bad Request'

def handle_join_room(body):
    """Handle join room request"""
    try:
        data = json.loads(body)
        username = data.get('username')
        room_name = data.get('room')
        room_key = data.get('key', '')
        conn_id = data.get('conn_id')
        
        if not username or not room_name:
            return json.dumps({'error': 'Username and room required'}), '400 Bad Request'
        
        if room_name not in chat_rooms:
            return json.dumps({'error': 'Room does not exist'}), '400 Bad Request'
        
        room = chat_rooms[room_name]
        
        if room['key'] and room['key'] != room_key:
            return json.dumps({'error': 'Invalid room key'}), '403 Forbidden'
        
        # Add user to room
        if conn_id in active_connections:
            active_connections[conn_id]['name'] = username
            active_connections[conn_id]['room'] = room_name
            room['users'][conn_id] = username
        
        # Get user list
        user_list = list(room['users'].values())
        
        return json.dumps({
            'success': True,
            'room': room_name,
            'users': user_list,
            'messages': room['messages'][-50:]  # Last 50 messages
        }), '200 OK'
    except Exception as e:
        print('Join error:', e)
        return json.dumps({'error': 'Server error'}), '500 Internal Server Error'

def handle_send_message(body):
    """Handle send message"""
    try:
        data = json.loads(body)
        conn_id = data.get('conn_id')
        message_text = data.get('message')
        
        if conn_id not in active_connections:
            return json.dumps({'error': 'Not in room'}), '400 Bad Request'
        
        user_data = active_connections[conn_id]
        room_name = user_data['room']
        username = user_data['name']
        
        if not room_name or room_name not in chat_rooms:
            return json.dumps({'error': 'Not in valid room'}), '400 Bad Request'
        
        timestamp = time.time()
        message = {
            'username': username,
            'message': message_text,
            'timestamp': timestamp
        }
        
        # Store message
        chat_rooms[room_name]['messages'].append(message)
        
        # Keep only last 100 messages
        if len(chat_rooms[room_name]['messages']) > 100:
            chat_rooms[room_name]['messages'] = chat_rooms[room_name]['messages'][-100:]
        
        return json.dumps({
            'success': True,
            'message': message
        }), '200 OK'
    except Exception as e:
        print('Message error:', e)
        return json.dumps({'error': 'Server error'}), '500 Internal Server Error'

def handle_get_updates(body):
    """Poll for updates (messages, users)"""
    try:
        data = json.loads(body)
        conn_id = data.get('conn_id')
        last_msg_id = data.get('last_msg_id', 0)
        
        if conn_id not in active_connections:
            return json.dumps({'error': 'Not connected'}), '400 Bad Request'
        
        user_data = active_connections[conn_id]
        room_name = user_data.get('room')
        
        if not room_name or room_name not in chat_rooms:
            return json.dumps({'messages': [], 'users': []}), '200 OK'
        
        room = chat_rooms[room_name]
        
        # Get new messages
        new_messages = room['messages'][last_msg_id:]
        user_list = list(room['users'].values())
        
        return json.dumps({
            'messages': new_messages,
            'users': user_list,
            'msg_count': len(room['messages'])
        }), '200 OK'
    except Exception as e:
        print('Update error:', e)
        return json.dumps({'error': 'Server error'}), '500 Internal Server Error'

def handle_leave_room(body):
    """Handle leave room"""
    try:
        data = json.loads(body)
        conn_id = data.get('conn_id')
        
        if conn_id in active_connections:
            user_data = active_connections[conn_id]
            room_name = user_data.get('room')
            
            if room_name and room_name in chat_rooms:
                if conn_id in chat_rooms[room_name]['users']:
                    del chat_rooms[room_name]['users'][conn_id]
            
            active_connections[conn_id]['room'] = None
        
        return json.dumps({'success': True}), '200 OK'
    except:
        return json.dumps({'error': 'Server error'}), '500 Internal Server Error'

def handle_register(body):
    """Register a connection and get conn_id"""
    global conn_counter
    conn_counter += 1
    conn_id = f"conn_{conn_counter}"
    
    active_connections[conn_id] = {
        'name': None,
        'room': None,
        'last_seen': time.time()
    }
    
    return json.dumps({
        'success': True,
        'conn_id': conn_id
    }), '200 OK'

def cleanup_stale_connections():
    """Remove inactive connections"""
    current_time = time.time()
    to_remove = []
    
    for conn_id, data in active_connections.items():
        if current_time - data.get('last_seen', 0) > 300:  # 5 minutes timeout
            to_remove.append(conn_id)
    
    for conn_id in to_remove:
        if conn_id in active_connections:
            room_name = active_connections[conn_id].get('room')
            if room_name and room_name in chat_rooms:
                if conn_id in chat_rooms[room_name]['users']:
                    del chat_rooms[room_name]['users'][conn_id]
            del active_connections[conn_id]
    
    if to_remove:
        print(f'Cleaned up {len(to_remove)} stale connections')

def start_server():
    """Start HTTP server"""
    ip = connect_wifi()
    if not ip:
        return
    
    # Create default room
    chat_rooms['General'] = {
        'key': '',
        'users': {},
        'messages': []
    }
    
    # Create socket
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    s.setblocking(False)
    
    print('Server running on:', ip)
    print('Access at: http://' + ip)
    
    last_cleanup = time.time()
    
    while True:
        try:
            # Periodic cleanup
            if time.time() - last_cleanup > 60:
                cleanup_stale_connections()
                last_cleanup = time.time()
            
            # Accept connection
            try:
                conn, addr = s.accept()
                conn.settimeout(2.0)
            except OSError:
                time.sleep(0.1)
                continue
            
            try:
                # Receive data
                data = conn.recv(2048)
                if not data:
                    conn.close()
                    continue
                
                method, path, headers, body = parse_http_request(data)
                
                if not method:
                    conn.close()
                    continue
                
                # Handle OPTIONS (CORS preflight)
                if method == 'OPTIONS':
                    response = create_response('200 OK', 'text/plain', '')
                    conn.send(response.encode())
                    conn.close()
                    continue
                
                # Route handling
                if path == '/api/rooms' and method == 'GET':
                    body = handle_get_rooms()
                    response = create_response('200 OK', 'application/json', body)
                
                elif path == '/api/rooms/create' and method == 'POST':
                    body, status = handle_create_room(body)
                    response = create_response(status, 'application/json', body)
                
                elif path == '/api/register' and method == 'POST':
                    body, status = handle_register(body)
                    response = create_response(status, 'application/json', body)
                
                elif path == '/api/join' and method == 'POST':
                    body, status = handle_join_room(body)
                    response = create_response(status, 'application/json', body)
                
                elif path == '/api/message' and method == 'POST':
                    body, status = handle_send_message(body)
                    response = create_response(status, 'application/json', body)
                
                elif path == '/api/updates' and method == 'POST':
                    body, status = handle_get_updates(body)
                    response = create_response(status, 'application/json', body)
                
                elif path == '/api/leave' and method == 'POST':
                    body, status = handle_leave_room(body)
                    response = create_response(status, 'application/json', body)
                
                elif path == '/api/health' and method == 'GET':
                    body = json.dumps({
                        'status': 'online',
                        'rooms': len(chat_rooms),
                        'users': len(active_connections)
                    })
                    response = create_response('200 OK', 'application/json', body)
                
                else:
                    body = json.dumps({'error': 'Not found'})
                    response = create_response('404 Not Found', 'application/json', body)
                
                conn.send(response.encode())
                conn.close()
                
            except Exception as e:
                print('Request error:', e)
                try:
                    conn.close()
                except:
                    pass
        
        except Exception as e:
            print('Server error:', e)
            time.sleep(1)

# Run server
if __name__ == '__main__':
    start_server()
